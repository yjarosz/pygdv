# -*- coding: utf-8 -*-

"""WebHelpers used in pygdv."""

from webhelpers import date, feedgenerator, html, number, misc, text

import genshi
from tg import url
from pygdv.lib import constants

def get_delete_link(obj_id, rights = None):
    '''
    Get an HTML delete link for an object.
    @param obj_id: the object_id
    @type obj_id: an integer
    @return: the HTML link
    '''
    if rights is not None and constants.right_upload in rights :
        if rights[constants.right_upload]:
            return '''
    <form method="POST" action=%s class="button-to">
    <input name="_method" value="DELETE" type="hidden"/>
   
    <input class="action delete-button" onclick="return confirm('Are you sure?');" 
        value="delete" style="background-color: transparent; float:left; 
        border:0; color: #286571; display: inline; margin: 0; padding: 0;" 
    type="submit"/>
    </form>
        ''' % (obj_id)
    return ''
        
def get_view_link(obj_id, param, rights = None):
    '''
    Return a HTML view link.
    
    '''
    if rights is not None:
        return ''' <a class='action view_link' href="%s"></a>''' % url('./view', params={'project_id':obj_id})
    return ''

def get_export_link(obj_id, param='track_id', rights=None):
    '''
    Return a HTML export link.
    '''
    if rights is not None:
        return ''' <a class='action export_link' href="%s"></a>''' % url('/tracks/export', params={param:obj_id})
    return ''

def get_share_link(obj_id, param, rights = None):
    '''
    Return a HTML share link.
    '''
    if rights is not None and constants.right_upload in rights :
        if rights[constants.right_upload]:
            return ''' <a class='action share_link' href="%s"></a>''' % url('./share', params={param:obj_id})
    return ''
                                                        
def get_edit_link(obj_id, rights = None, link=''):
    edit = url('%s%s/edit' % (link, obj_id))
    print edit
    if rights is not None and constants.right_upload in rights :
        if rights[constants.right_upload]:
            return '''
    <a class="action edit_link" href="%s%s/edit" style="text-decoration:none"></a>
           ''' % (link, obj_id)
    return ''

def get_detail_link(obj_id, param, rights = None):
    
    if rights is not None and (constants.right_download in rights and rights[constants.right_download]):
            return '''
    <a class="action detail_link" href="%s" style="text-decoration:none"></a>
           ''' % url('./detail', params={param:obj_id})
    return ''
       
def get_right_checkbok(obj, right_name):
    circle = obj.circle
    rights = obj.rights
    checked = False
    for right in rights :
        if right.name == right_name : 
            checked = True
    str = '''
    <input type="checkbox" name="rights_checkboxes" value="%s"
   
''' % (right_name)
    
    if checked :
        str+=' checked="yes"'
    str+='/><label >%s</label>' % (right_name)
    return str





'''

<input type="checkbox" name="rights_checkboxes" value="Download" id="rights_checkboxes_1">
                        <label for="rights_checkboxes_1">Download</label>
                        </td><td>
                        <input type="checkbox" name="rights_checkboxes" value="Upload" id="rights_checkboxes_2">
                        <label for="rights_checkboxes_2">Upload</label>
                        
                        '''





def get_project_right_sharing_form(circle_right):
    options = ['Read', 'Download', 'Upload']
    str = '''
    <form class="required rightsharingform" method="post" action="post_share">
    <div><input type="hidden" value="%s" name='circle_id' class="hiddenfield"></div>
    <div><input type="hidden" value="%s" name='project_id' class="hiddenfield"></div>
    <table cellspacing="0" cellpadding="2" border="0">
        <tbody>
            <tr title="" id="rights_checkboxes.container">    
                <td class="fieldcol">
                    <table class="checkboxtable" id="rights_checkboxes">
                        <tbody>
                            <tr>
                                ''' % (circle_right.circle.id, circle_right.project_id)
    for opt in options:
        str+='<td>'+get_right_checkbok(circle_right, opt)+'</td>'
        
        
    str+='''
                        
                            </tr>
                        </tbody>
                    </table>
                </td>
            <td class="fieldcol" id="submit.container">
                <input type="submit" value="change rights" class="submitbutton">
            </td>
        </tr>
    </tbody></table>
</form>
''' 
    return str



def get_task_status(track=None):
    '''
    Get a output for the status of a task : a link to the traceback if the status is ``FAILURE``,
    else the string representing the status.
    @param track : the track to get the status from
    '''
    obj = track
    if obj.status != constants.ERROR: return obj.status
    return genshi.Markup('<a href="%s">%s</a>' % (url('./traceback', params={'track_id':obj.id}),
                                                  constants.ERROR
                                                  ))



