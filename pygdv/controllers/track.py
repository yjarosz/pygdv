"""Track Controller"""
from __future__ import absolute_import

from tgext.crud import CrudRestController


from repoze.what.predicates import not_anonymous, has_any_permission, has_permission
import tg, sys, traceback
from tg import expose, flash, require, tmpl_context, validate, request, response
from tg.controllers import redirect
from tg.decorators import with_trailing_slash

from pygdv.model import DBSession, Track, Sequence, Input, Task
from pygdv.widgets.track import track_table, track_export, track_table_filler, track_new_form, track_edit_filler, track_edit_form, track_grid, default_track_form
from pygdv import handler
from pygdv.lib import util, constants, checker, reply
from pygdv.celery import tasks
import tempfile, track

__all__ = ['TrackController']


class TrackController(CrudRestController):
    allow_only = has_any_permission(constants.perm_user, constants.perm_admin)
    model = Track
    table = track_table
    table_filler = track_table_filler
    edit_form = track_edit_form
    new_form = track_new_form
    edit_filler = track_edit_filler







    @with_trailing_slash
    @expose('pygdv.templates.list')
    @expose('json')
    #@paginate('items', items_per_page=10)
    def get_all(self, *args, **kw):
        user = handler.user.get_user_in_session(request)

        #tracks = DBSession.query(TMPTrack).filter(TMPTrack.user_id == user.id).all()

        tracks = user.tracks
        data = [util.to_datagrid(track_grid, tracks, "Track Listing", len(tracks)>0)]
        t = handler.help.tooltip['track']
        return dict(page='tracks', model='track', form_title="new track", items=data, value=kw, tooltip=t)



    @require(not_anonymous())
    @expose('pygdv.templates.form')
    def new(self, *args, **kw):
        tmpl_context.widget = track_new_form
        return dict(page='tracks', value=kw, title='new Track')


    @expose('json')
    def create(self, *args, **kw):
        """
        Entry point for creating track

        """
        print 'CREATE TRACK %s, %s' % (args, kw)


        user = handler.user.get_user_in_session(request)
        # change a parameter name
        if kw.has_key('assembly'):
            kw['sequence_id']=kw.get('assembly')
            del kw['assembly']
        if kw.has_key('urls'):
            kw['url']=kw.get('urls')
            del kw['urls']
        # verify track parameters
        try :
            handler.track.pre_track_creation(url=kw.get('url', None),
                file_upload=kw.get('file_upload', None),
                fsys=kw.get('fsys', None),
                project_id=kw.get('project_id', None),
                sequence_id=kw.get('sequence_id', None))
        except Exception as e:
            return reply.error(request, str(e), tg.url('./new'), {})


        # get parameters
        track_name, extension, sequence_id = handler.track.fetch_track_parameters(
            url=kw.get('url', None),
            file_upload=kw.get('file_upload', None),
            fsys=kw.get('fsys', None),
            trackname=kw.get('trackname', None),
            extension=kw.get('extension', None),
            project_id=kw.get('project_id', None),
            sequence_id=kw.get('sequence_id', None))
                
        # upload the track it's from file_upload
        if request.environ[constants.REQUEST_TYPE] == constants.REQUEST_TYPE_BROWSER :
            fu = kw.get('file_upload', None)
            if fu is not None:
                kw['uploaded']=True
                _f = util.download(file_upload=fu,
                    filename=track_name, extension=extension)
                kw['file']=_f.name
                del kw['file_upload']

        # create a new track
        _track = handler.track.new_track(user.id, track_name, sequence_id=sequence_id, admin=False, project_id=kw.get('project_id', None))

        # format parameters
        _uploaded = kw.get('uploaded', False)
        _file = kw.get('file', None)
        _urls = kw.get('url', None)
        _fsys=kw.get('fsys', None)
        _track_name = track_name
        _extension = extension
        _callback_url = constants.callback_track_url()
        _force = kw.get('force', False)
        _track_id = _track.id
        _user_key = user.key
        _user_mail = user.email

        # launch task with the parameters
        async = tasks.track_input.delay(_uploaded, _file, _urls, _fsys, _track_name, _extension, _callback_url, _force, _track_id, _user_mail, _user_key, sequence_id)
        
        # update the track
        handler.track.update(track=_track, params={'task_id' : async.task_id})

        return reply.normal(request, 'Processing launched.', './', {'task_id' : async.task_id,
                                                                    'track_id' : _track.id})

    @expose('json')
    @validate(track_new_form, error_handler=new)
    def post(self, *args, **kw):
#        user = handler.user.get_user_in_session(request)
#
#
#
#
#        if 'file_upload' in kw and kw['file_upload'] is not None:
#            filename = kw ['file_upload'].filename
#        elif 'urls' in kw :
#            import urlparse
#            filename = kw['urls'].split('/')[-1]
#            u = urlparse.urlparse(kw['urls'])
#            if not u.hostname:
#                url = 'http://%s' % kw['urls']
#                u = urlparse.urlparse(url)
#                if u.hostname:
#                    kw['urls'] = url
#                else :
#                    flash("Bad file/url", 'error')
#                    raise redirect('./')
#
#        tmp_track = TMPTrack()
#        tmp_track.name = filename
#        tmp_track.sequence_id = kw['assembly']
#        tmp_track.user_id = user.id
#        DBSession.add(tmp_track)
#        DBSession.flush()
#
#        kw['tmp_track_id'] = tmp_track.id
        return self.create(*args, **kw)


    @expose('genshi:tgext.crud.templates.post_delete')
    def post_delete(self, *args, **kw):
        user = handler.user.get_user_in_session(request)
        _id = args[0]
#        tmp = kw.get('tmp', 'False')
#        if tmp in ['True']:
#            tmp_track = DBSession.query(TMPTrack).filter(TMPTrack.id == _id).first()
#            DBSession.delete(tmp_track)
#            DBSession.flush()
        if not checker.can_edit_track(user, _id) and not checker.user_is_admin(user.id):
            flash("You haven't the right to edit any tracks which is not yours")
            raise redirect('../')
        handler.track.delete_track(track_id=_id)
        raise redirect('./')


    @expose('pygdv.templates.track_form')
    def edit(self, *args, **kw):
        track = DBSession.query(Track).filter(Track.id == args[0]).first()
        tmpl_context.widget = track_edit_form
        tmpl_context.color = track.parameters.color
        kw['name']=track.name

        return dict(title='Edit track', page='track', color=track.parameters.color, value=kw)
        #CrudRestController.edit(self, *args, **kw)

    @expose()
    @validate(track_edit_form, error_handler=edit)
    def put(self, *args, **kw):
        user = handler.user.get_user_in_session(request)
        _id = args[0]

        if not checker.can_edit_track(user, _id) and not checker.user_is_admin(user.id):
            flash("You haven't the right to edit any tracks which is not yours")
            raise redirect('../')

        track = DBSession.query(Track).filter(Track.id == _id).first()
        track.name = kw['name']
        print kw
        if 'color' in kw:
            track.parameters.color = kw['color']
        DBSession.flush()
        redirect('../')



    @expose('pygdv.templates.track_export')
    def export(self, track_id, *args, **kw):
        user = handler.user.get_user_in_session(request)
        if not checker.can_download_track(user.id, track_id)  and not checker.user_is_admin(user.id):
            flash("You haven't the right to export any tracks which is not yours")
            raise redirect('../')
        track = DBSession.query(Track).filter(Track.id == track_id).first()

        data = util.to_datagrid(track_grid, [track])
        tmpl_context.form = track_export
        kw['track_id']=track_id
        return dict(page='tracks', model='Track', info=data, form_title='', value=kw)

    @expose()
    def dump(self, track_id, format,  *args, **kw):
        user = handler.user.get_user_in_session(request)
        if not checker.can_download_track(user.id, track_id)  and not checker.user_is_admin(user.id):
            flash("You haven't the right to export any tracks which is not yours")
            raise redirect('../')
        _track = DBSession.query(Track).filter(Track.id == track_id).first()
        if format == 'sqlite':
            response.content_type = 'application/x-sqlite3'
            return open(_track.path).read()
        else :
            tmp_file = tempfile.NamedTemporaryFile(delete=True)
            tmp_file.close()
            track.convert(_track.path, (tmp_file.name, format))
            response.content_type = 'text/plain'
            return open(tmp_file.name).read()

    @expose()
    def link(self, track_id, *args, **kw):
        user = handler.user.get_user_in_session(request)
        if not checker.user_own_track(user.id, track_id)  and not checker.user_is_admin(user.id):
            flash("You haven't the right to download any tracks which is not yours")
        track = DBSession.query(Track).filter(Track.id == track_id).first()
        response.content_type = 'application/x-sqlite3'
        return open(track.path).read()



    @expose()
    def traceback(self, track_id, tmp):
        user = handler.user.get_user_in_session(request)
        if tmp in ['True']:
            return DBSession.query(TMPTrack).filter(TMPTrack.id == track_id).first().traceback


        elif not checker.user_own_track(user.id, track_id) and not checker.user_is_admin(user.id):

            flash("You haven't the right to look at any tracks which is not yours")
            raise redirect('./')
        track = DBSession.query(Track).filter(Track.id == track_id).first()
        return track.traceback

    @expose()
    def copy(self, track_id):
        user = handler.user.get_user_in_session(request)
        if not checker.can_download_track(user.id, track_id):
            return reply.error(request, 'You have no right to copy this track in your profile.', './', {})
        t = DBSession.query(Track).filter(Track.id == track_id).first()
        if not t:
            return reply.error(request, 'No track with this id.', './', {})
        handler.track.copy_track(user.id, t)
        return reply.normal(request, 'Copy successfull', './', {})




    ##### for ADMINS #######




    @require(has_permission('admin', msg='Only for admins'))
    @expose('pygdv.templates.form')
    def default_tracks(self, **kw):
        tmpl_context.widget = default_track_form
        return dict(page='tracks', value=kw, title='new default track (visible on all projects with the same assembly)')

    @expose()
    @require(has_permission('admin', msg='Only for admins'))
    @validate(default_track_form, error_handler=default_tracks)
    def default_tracks_upload(self, *args, **kw):
        user = handler.user.get_user_in_session(request)
        kw['admin'] = True
        util.file_upload_converter(kw)

        task_id = tasks.process_track.delay(user.id, **kw)
        return reply.normal(request, 'Task launched.', '/home', {'task_id' : task_id})

    @require(has_permission('admin', msg='Only for admins'))
    @expose('pygdv.templates.list')
    def admin(self, **kw):
        sequences = DBSession.query(Sequence).all()
        tracks = []
        for sequence in sequences:
            tracks += sequence.default_tracks
        data = [util.to_datagrid(track_grid, tracks, "Track Listing", len(tracks)>0)]

        return dict(page='tracks', model='track', form_title="admin tracks",items=data,value=kw)

    @require(has_permission('admin', msg='Only for admins'))
    @expose('pygdv.templates.list')
    def all(self, *args, **kw):
        if 'user_id' in kw:
            tracks = DBSession.query(Track).filter(Track.user_id == kw['user_id']).all()
        else :
            tracks = DBSession.query(Track).all()
        data = [util.to_datagrid(track_grid, tracks, "Track Listing", len(tracks)>0)]
        return dict(page='tracks', model='track', form_title="new track",items=data,value=kw)






    @expose('json')
    def after_sha1(self, fname, sha1, force, callback_url, track_id, old_task_id, mail, key, sequence_id, extension, trackname):
        """
        Called after a sha1 where calculated on a file.
        If the sha1 already exist, only the databases operations are done.
        Else the input will go in the second part of the process.
        The input can be 'forced' to be recomputed
        """
        try :
            print '[x] after sha1 [x] %s and %s' % (fname, sha1)
            _input = DBSession.query(Input).filter(Input.sha1 == sha1).first()
            do_process = True
            if util.str2bool(force) and _input is not None :
                handler.track.delete_input(_input.sha1)
                DBSession.delete(_input)
                DBSession.flush()
            elif _input is not None:
                do_process = False
                handler.track.update(track_id=track_id,
                    params={'new_input_id' : _input.id})
                handler.track.finalize_track_creation(track_id=track_id)

            if do_process :

                handler.track.update(track_id=track_id, params={'sha1' : sha1})
                sequence = DBSession.query(Sequence).filter(Sequence.id == sequence_id).first()
                async = tasks.track_process.delay(mail, key, old_task_id, fname, sha1, callback_url, track_id, sequence.name, extension, trackname, callback_url)

                handler.track.update(track_id=track_id,
                    params={'new_task_id' : async.task_id})
            return {'success' : 'to second process'}
        except Exception as e:
            etype, value, tb = sys.exc_info()
            traceback.print_exception(etype, value, tb)


            return {'error' : str(e)}


    @expose('json')
    def after_process(self, mail, key, old_task_id, track_id, datatype):
        print '[x] after process [x] %s' % track_id
        task = DBSession.query(Task).filter(Task.task_id == old_task_id).first()
        if task is not None :
            DBSession.delete(task)
            DBSession.flush()
        if not track_id == 'None':
            handler.track.update(track_id=track_id, params={'datatype' : datatype})
            handler.track.finalize_track_creation(track_id=track_id)
        return {'success' : 'end'}