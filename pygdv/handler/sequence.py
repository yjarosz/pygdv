from tg import app_globals as gl
from pygdv.lib import util
from pygdv.handler import track

def add_new_sequence(user_id, sequence):
    '''
    Method called when a new sequence is created on GDV.
    It should import fast from JBrowsoR
    '''
    file_url = gl.genrep.get_sqlite_file(sequence)
    files = util.upload(url=file_url)
    if len(files) > 0:
         filename, tmp_file = files[0]
         track.create_track(user_id, sequence, trackname='Genes', f=tmp_file.name, admin=True)
    
    
    


