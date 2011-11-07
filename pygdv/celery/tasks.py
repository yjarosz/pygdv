from __future__ import absolute_import
from celery.task import task, chord, subtask, TaskSet
import shutil, os, sys, traceback
from pygdv.lib.jbrowse import jsongen, scores
from pygdv.lib.constants import json_directory, track_directory
from celery.result import AsyncResult
from pygdv.lib import constants
import track
import tempfile

success = 1


#############################################################################################################
#        FILE PROCESSING
#############################################################################################################

@task(max_retries=1)
def del_file_on_error(tasks, sha1, *args, **kw):
    '''
    Verify if the file are well processed.
    If no, it will erase the directory created in the
    tracks directory
    @param tasks : a list of return result. If one is different from 1, the directory is erased.
    '''
    print 'del file on error tasks :%s, sha1 : %s in %s and %s' % (tasks, sha1, track_directory(), json_directory())
    for theid in tasks:
        if not theid == success :
            print 'sha1 : ' + sha1
            path1 = os.path.join(track_directory(), sha1, '.sql')
            path2 = os.path.join(json_directory(), sha1, '.sql')
            shutil.rmtree(path1, ignore_errors = True)
            shutil.rmtree(path2, ignore_errors = True)
            raise theid
    return 1

@task()
def del_tmp_file(f):
    return 1
    print 'deleting temporary file'
    try:
        os.remove(os.path.abspath(f))
    except OSError :
        pass
    return 1

def process_signal(database, sha1, name):
    '''
    Process a ``signal`` SQL file and create the databases needed by JBrowse.
    @param database : the database
    @param sha1 : the sah1 of the file
    '''
    print '[t] starting task ``process signal`` : db (%s), sha1(%s), name(%s).' % (database, sha1, name)
    output_dir = json_directory()
    callback = subtask(task=del_file_on_error, args=(sha1, output_dir))
    
    t1 = _compute_scores.subtask((database, sha1, output_dir))
    t2 = _jsonify_signal.subtask((sha1, output_dir, database))
    
    job = chord(tasks=[t1,t2])(callback)
    return job  


def process_features(database, sha1, name, extended = False): 
    '''
    Process a ``features`` SQL file and create the databases needed by JBrowse.
    @param database : the database
    @param sha1 : the sah1 of the file
    @param name : the name of the output track
    @param extended : if the SQLite database is 'extended' format
    '''
    print '[t] starting task ``process features`` : db (%s), sha1(%s), name(%s), extended(%s).' % (database, sha1, name, extended)
    output_dir = json_directory()
    callback = subtask(task=del_file_on_error, args=(sha1, output_dir))
    
    return _jsonify_features.delay(database, name, sha1, output_dir, '/data/jbrowse', '', extended,
                            callback=callback)
    
#    job = chord(tasks = [
#            _jsonify_features.subtask((database, name, sha1, output_dir, '/data/jbrowse', '', extended))
#                   ])(callback)
#    return job





@task()
def _compute_scores(database, sha1, output_dir, callback=None, callback_on_error=None):
    '''
    Launch the process to pre-calculate scores on a signal database.
    '''
    print '[t] starting task ``compute scores`` : db (%s), sha1(%s)' % (database, sha1)
    try :
        scores.pre_compute_sql_scores(database, sha1, output_dir)
        if callback : 
            output_dir = json_directory()
            return subtask(callback).delay(sha1, output_dir, database, callback_on_error=callback_on_error)
    except Exception as e:
        etype, value, tb = sys.exc_info()
        traceback.print_exception(etype, value, tb)
        if callback_on_error :
            subtask(callback).delay([e], sha1)
        raise e


@task()
def _jsonify_signal(sha1, output_root_directory, database_path, callback_on_error=None, del_tmp=None):
    '''
    Launch the process to produce a JSON output for a ``signal`` database.
    '''
    print 'jsonify signal sha1 : %s, output dir : %s, path : %s ' % (sha1, output_root_directory, database_path)
    try :
        jsongen.jsonify_quantitative(sha1, output_root_directory, database_path)
    except Exception as e:
        etype, value, tb = sys.exc_info()
        traceback.print_exception(etype, value, tb)
        if callback_on_error :
            subtask(callback_on_error).delay([e], sha1)
            raise e
    return 1


@task()
def _jsonify_features(database, name, sha1, output_dir, public_url, browser_url, extended, callback_on_error=None):
    '''
    Launch the process to produce a JSON output for a ``feature`` database.
    '''
    try :
        jsongen.jsonify(database, name, sha1, output_dir, public_url, browser_url, extended)
    except Exception as e:
        etype, value, tb = sys.exc_info()
        traceback.print_exception(etype, value, tb)
        if callback_on_error :
            subtask(callback_on_error).delay([e], sha1)
            raise e
    return 1

simple_fields = ('start', 'end', 'score', 'name', 'strand')
ext_fields = ('start', 'end', 'score', 'name', 'strand', 'type', 'id')
agg_field = 'attributes'
signal_fields = ('start', 'end', 'score')

@task()
def convert(path, dst, sha1, datatype, assembly_name, name, tmp_file, format, process_db=None, callback_on_error=None):
    
    tfile = tempfile.NamedTemporaryFile(suffix='.sql', delete=True)
    tmp_dst = tfile.name
    tfile.close()
    try:
        # normal convert
        print 'convert %s to %s' %(path, tmp_dst)
        track.convert(path, tmp_dst)
        
        
        # then tranform to GDV format
        if datatype == constants.SIGNAL:
            f = signal_fields
            with track.load(tmp_dst, 'sql', readonly=True) as t:
                with track.new(dst, 'sql') as t2:
                    for chrom in t:
                        ## TODO
                        t2.write(chrom, t.read(chrom, fields=signal_fields), fields=signal_fields)
                    t2.assembly = assembly_name
                    
        elif datatype == constants.FEATURES:
            f = simple_fields
            with track.load(tmp_dst, 'sql', readonly=True) as t:
                with track.new(dst, 'sql') as t2:
                    for chrom in t:
                        gen = track.common.aggregate(t, f)
                        t2.write(chrom, gen, fields=f + (agg_field,))
                    t2.assembly = assembly_name
                
        
        elif datatype == constants.RELATIONAL:
            f = ext_fields
            with track.load(tmp_dst, 'sql', readonly=True) as t:
                with track.new(dst, 'sql') as t2:
                    for chrom in t:
                        gen = track.common.aggregate(t, f,  fields=f + (agg_field,))
                        t2.write(chrom, gen)
                    t2.assembly = assembly_name
        
        try:
            os.remove(os.path.abspath(path))
        except OSError :
            pass
        try:
            os.remove(os.path.abspath(tmp_dst))
        except OSError :
            pass
        
        
        if process_db :
            return subtask(process_db).delay(datatype, assembly_name, dst, sha1, name, format)
        
    except Exception as e:
        etype, value, tb = sys.exc_info()
        traceback.print_exception(etype, value, tb)
        if callback_on_error :
            subtask(callback_on_error).delay([e], sha1)
            raise e
    return 1


@task()
def process_database(datatype, assembly_name, path, sha1, name, format):
    
    dispatch = _sql_dispatch.get(datatype, lambda *args, **kw : cannot_process(*args, **kw))
    return dispatch(path, sha1, name)
    
    



def cannot_process():
    print '[x] ERROR [x] cannot process'
    return -1;
    
    
    


    

def _signal(path, sha1, name):
    '''
    Task for a ``signal`` database.
    @return the subtask associated
    '''
    output_dir = json_directory()
    callback_on_error = subtask(task=del_file_on_error, args=(sha1,))
    t1 = _compute_scores.delay(path, sha1, output_dir, callback=subtask(_jsonify_signal), 
                                     callback_on_error=callback_on_error)
    return t1

def _features(path, sha1, name):
    '''
    Task for a ``feature`` database.
    @return the subtask associated
    '''
    output_dir = json_directory()
    callback_on_error = subtask(task=del_file_on_error, args=(sha1,))
    
    t1 = _jsonify_features.delay(path, name, sha1, output_dir, '/data/jbrowse', '', False,
                            callback_on_error=callback_on_error)
    return t1
    

def _relational(path, sha1, name):
    '''
    Task for a ``relational`` database
    @return the subtask associated
    '''
    output_dir = json_directory()
    callback_on_error = subtask(task=del_file_on_error, args=(sha1,))
    
    t1 = _jsonify_features.delay(path, name, sha1, output_dir, '/data/jbrowse', '', True,
                            callback_on_error=callback_on_error)
    return t1
    
    
    

'''
_sql_dispatch : will choose in which process the database will go, based on it's datatype 
'''  
    
_sql_dispatch = {'quantitative' : lambda *args, **kw : _signal(*args, **kw),
                 constants.SIGNAL : lambda *args, **kw : _signal(*args, **kw),
                 
                 'qualitative' :  lambda *args, **kw : _features(*args, **kw),
                 constants.FEATURES :  lambda *args, **kw : _features(*args, **kw),
                 
                 'extended' :  lambda *args, **kw : _relational(*args, **kw),
                  constants.RELATIONAL :  lambda *args, **kw : _relational(*args, **kw)
                 }
    
