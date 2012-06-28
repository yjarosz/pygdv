from pygdv.model import DBSession, Project, User, Track, Circle, Right, Group, Job
from pygdv.lib import constants
from sqlalchemy.sql import and_, or_


def can_edit_track(user, track_id):
    for track in user.tracks :
        if int(track_id) == track.id : return True
    if user_is_admin(user.id) : return True
    track = DBSession.query(Track).filter(Track.id == track_id).first()
    for project in track.projects:
        if check_permission(project=project, user=user, right_id=constants.right_upload_id) : return True
    return False
            
def check_permission(project=None, project_id=None, user=None, user_id=None, right_id=None):
    if project is None:
        project = DBSession.query(Project).filter(Project.id == project_id).first()
    if project is None: return False
    if user is None:
        user = DBSession.query(User).filter(User.id == user_id).first()

    if own(user=user, project=project) : return True

    for circle, rights in project.circles_with_rights.iteritems():
        if right_id in [r.id for r in rights] and circle in user.circles: return True
    return False

def own(user=None, user_id=None, project=None, project_id=None):
    if user_id is None:
        user_id = user.id
    if project is None:
        project = DBSession.query(Project).filter(Project.id == project_id).first()
    return project.user_id == user_id

def is_admin(user=None, user_id=None):
    if user is None:
        user = DBSession.query(User).filter(User.id == user_id).first()
    admin_group = DBSession.query(Group).filter(Group.name == constants.group_admins).first()
    return user in admin_group.users






def user_own_project(user_id, project_id):
    '''
    Look if the user own the project 
    '''
    project = DBSession.query(Project).filter(Project.id == project_id).first()
    if project is not None:
        return project.user_id == user_id
    return False

def user_own_track(user_id, track_id):
    '''
    Look if the user own the track 
    '''
    track = DBSession.query(Track).filter(Track.id == track_id).first()
    if track is not None : return track.user_id == user_id
    return False

def user_own_circle(user_id, circle_id):
    '''
    Look if the user own the circle.
    '''
    circle = DBSession.query(Circle).filter(Circle.id == circle_id).first()
    if circle.creator_id == user_id: return True
    if circle.admin :
        user = DBSession.query(User).filter(User.id == user_id).first()
        admin_group = DBSession.query(Group).filter(Group.name == constants.group_admins).first()
        return user in admin_group.users
    return False

def user_is_admin(user_id):
    user = DBSession.query(User).filter(User.id == user_id).first()
    admin_group = DBSession.query(Group).filter(Group.name == constants.group_admins).first()
    return user in admin_group.users

def check_permission_project(user_id, project_id, right_id):
    project = DBSession.query(Project).filter(Project.id == project_id).first()
    if project is None:
        return False
    if not user_own_project(user_id, project_id) and not user_is_admin(user_id):
        p = DBSession.query(Project).join(
                                Project._circle_right).join(Right).join(User.circles).filter(
                and_(User.id == user_id, Project.id == project_id, Right.id == right_id)
                ).first()
        return p != None
    return True

def can_download_track(user_id, track_id):
    if not user_own_track(user_id, track_id) and not user_is_admin(user_id):
        t = DBSession.query(Track).join(Project.tracks).filter(
            and_(Track.id == track_id, User.id == user_id)
            
             ).first()
        return t != None
    return True
    
def can_edit_job(user_id, job_id):
    if not user_is_admin(user_id):
        j = DBSession.query(Job).filter(and_(Job.id == job_id, Job.user_id == user_id)).first()
        return j != None
    return True
