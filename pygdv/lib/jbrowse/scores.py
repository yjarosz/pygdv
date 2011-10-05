
import math, sqlite3, shutil, os
import numpy as np
from pygdv.lib.util import float_equals
from pygdv.lib.jbrowse import TAB_WIDTH, zooms





def get_image_nb(position, zoom):
    '''
    Get the image number to put in the sqlite database.
    @param position : the position of the cursor
    @param zoom : the zoom
    @return an int
    '''
    return int(math.ceil(float(position)/TAB_WIDTH/zoom))


def get_tab_index(position, zoom):
    '''
    Get the index of the tab for the position specified.
    @param position : the position of the cursor
    @param zoom : the zoom
    '''
    return math.ceil(position/zoom)%TAB_WIDTH

def get_position_start(image_nb, tab_index, zoom):
    '''
    Get the start position on the genome from an image number, a tab index and a zoom
    '''
    return (image_nb * TAB_WIDTH + tab_index - TAB_WIDTH) * zoom

def get_position_end(image_nb, tab_index, zoom):
    '''
    Get the end position on the genome from an image number, a tab index and a zoom
    '''
    return (image_nb * TAB_WIDTH + tab_index - TAB_WIDTH) * zoom + zoom - 1 

    
def generate_array(cursor, max, max_zoom):
    '''
    Generate a numpy array that will represent the last feature on the cursor
    '''
    
    if max_zoom % max != 0:
        max = max_zoom - (max % max_zoom) + max
    array = np.zeros(max )
    for row in cursor :
        start = row[0]
        stop = row[1]
        score = row[2]
        
        img_nb_start = get_image_nb(start, 1)
        tab_index_start = get_tab_index(start, 1)
        
        img_nb_stop = get_image_nb(stop, 1)
        tab_index_stop = get_tab_index(stop, 1)
    
        index_start = img_nb_start * TAB_WIDTH + tab_index_start
        index_stop = img_nb_stop * TAB_WIDTH + tab_index_stop
        
        array[index_start:index_stop+1] = score
    return array

def gen_tuples(array, max, zoom):
    '''
    Generate the features (number, pos, score) to write in the db
    @param array : the array containning all scores
    @param max: the stop of the last feature
    @param zoom : the zoom level
    '''
    max_images = get_image_nb(max, zoom)
    tab_list = range(TAB_WIDTH)
    prev_score = None
    ## 'm im : %s' % max_images
    for i in range(1, max_images+1):
        for t in tab_list:
            index_start = get_position_start(i, t, zoom)
            index_end = get_position_end(i, t, zoom)
            if index_start > max :
                break
            ### 'i(%s), t(%s), z(%s), start %s, end %s' %(i, t, zoom, index_start, index_end)
            tmp = array[index_start:index_end+1]
            max_score = tmp.max()
            min_score = tmp.min()
            if(abs(max_score) - abs(min_score) < 0) :
                max_score = min_score
            if prev_score is None or not float_equals(prev_score, max_score):
                yield i, t, max_score
            prev_score = max_score
                    
                
                
    

    
def get_features(connection, chromosome):
    '''
    Get the features on a chromosome.
    @param chromosome : the chromosome
    @return a Cursor Object
    '''
    cursor = connection.cursor()
    return cursor.execute('select start, end, score from "%s"' % chromosome)

def get_chromosomes(connection):
    '''
    Get the chromosomes in the database
    '''
    cursor = connection.cursor()
    return cursor.execute("select name from chrNames;")

def write_tuples(conn, generator):
    '''
    Write tuples in the oupput specified.
    '''
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE sc (number INT, pos INT, score REAL)')
    cursor.executemany('insert into sc values (?, ?, ?);', generator)
    conn.commit()
    cursor.close()
    
def get_last_feature_stop(conn, chromosome):
    '''
    Get the stop of the last feature.
    '''
    cursor = conn.cursor()
    max = cursor.execute('select max(end) from "%s";' % chromosome).fetchone()[0]
    cursor.close()
    return max
           
def pre_compute_sql_scores(database, sha1, output_dir):
    ## 'prepare output directory'
    out_path = os.path.join(output_dir, sha1)
    os.mkdir(out_path)
    
    ## 'prepare connection'
    conn = sqlite3.connect(database)
    
    c = get_chromosomes(conn)
    
    for row in c:
        chromosome = row[0]
        ## 'getting max'
        max = get_last_feature_stop(conn, chromosome)
        ## 'getting features'
        features = get_features(conn, chromosome)
        ## 'generating score array'
        array = generate_array(features, max, 100000)
        features.close()
        
        for zoom in zooms:
            ## 'compute : zoom = %s' % zoom
            gen = gen_tuples(array, max, zoom)
            
            ## 'prepare output'
            output = os.path.join(out_path, '%s_%s.db' % (chromosome, zoom))
            out_connection = sqlite3.connect(output)
            
            ## 'write'
            write_tuples(out_connection, gen)
            
    c.close()
    conn.close()





import sys

if __name__ == '__main__':
    database = sys.argv[1]
    sha1 = sys.argv[2]
    output_dir = sys.argv[3]
    pre_compute_sql_scores(database, sha1, output_dir)
    
    












    