import hou
import shutil
import os

try:
    from PyQt5 import QtWidgets, QtCore, QtGui
except ImportError:
    from Qt import QtWidgets, QtCore, QtGui

def addVRayObjectIdParamTemplate( node ):
    parm_group = node.parmTemplateGroup()
    parm_folder = hou.FolderParmTemplate( 'folder', 'V-Ray Object' )
    parm_folder.addParmTemplate( hou.IntParmTemplate( 'vray_objectID', 'Object ID', 1 ) )
    parm_group.append( parm_folder )
    node.setParmTemplateGroup( parm_group )

def addSceneWirecolorVisualizer():
    if len( [visualizer for visualizer in hou.viewportVisualizers.visualizers( category=hou.viewportVisualizerCategory.Scene ) if visualizer.name() == 'wirecolor'] ) == 0:
        wirecolor_vis = hou.viewportVisualizers.createVisualizer( hou.viewportVisualizers.types()[1], category=hou.viewportVisualizerCategory.Scene )
        wirecolor_vis.setName( 'wirecolor' )
        wirecolor_vis.setLabel( 'Wirecolor' )
        wirecolor_vis.setParm( 'attrib', 'wirecolor' )
        wirecolor_vis.setParm( 'class', 3 )
        geoviewport = hou.ui.paneTabOfType( hou.paneTabType.SceneViewer ).curViewport()
        wirecolor_vis.setIsActive( True, viewport=geoviewport )

from_filename = ''
name = ''
object_id = 0
wirecolor = ( 0, 0, 0 )
handle = 0

clipboard = QtWidgets.QApplication.clipboard()
text = clipboard.text()
lines = text.splitlines()

#error_count = 0

if lines[0].startswith('#abc_export'):
    ls = lines[0].split(',', 2)
    fps = ls[1]
    range = ls[2]

    if fps != str(hou.fps()):
        print('warning: fps differs from export')
    if range != str(hou.playbar.timelineRange()):
        print('warning: animation range differs from export')

    geo_dir = hou.expandString('$HIP') + '/geo/'

    if not os.path.exists(geo_dir):
        os.makedirs(geo_dir)

    for line in lines[1:]:
        ls = line.split(',', 1)
        if len(ls) == 2:
            if ls[0] == 'name':
                name = ls[1]
            elif ls[0] == 'object_id':
                object_id = eval( ls[1] )
            elif ls[0] == 'wirecolor':
                wirecolor = eval( ls[1] )
            elif ls[0] == 'handle':
                handle = eval( ls[1] )
            elif ls[0] == 'filename':
                from_filename = ls[1]

                if os.path.isfile(from_filename):
                    to_filename = geo_dir + name + ".abc"

                    try:
                        shutil.move(from_filename, to_filename)
                    except IOError:
                        os.chmod( to_filename, 777 )  # ?? still can raise exception
                        shutil.move(from_filename, to_filename)

                    obj = hou.node( '/obj' )

                    geo = obj.node(name)
                    if geo == None:
                        geo = obj.createNode( 'geo' , name )
                        geo.moveToGoodPosition()
                        #geo.parm( 'scale' ).set( 0.01 )
                        addVRayObjectIdParamTemplate( geo )
                    geo.parm( 'vray_objectID' ).set( object_id )
                    geo.parm( 'use_dcolor' ).set( True )
                    geo.parm( 'dcolorr' ).set( wirecolor[0] )
                    geo.parm( 'dcolorg' ).set( wirecolor[1] )
                    geo.parm( 'dcolorb' ).set( wirecolor[2] )

                    file = geo.node( 'file1' )
                    if file != None:
                        file.destroy()

                    alembic = geo.node( 'alembic1' )
                    if alembic == None:
                        alembic = geo.createNode( 'alembic' )
                        alembic.moveToGoodPosition()
                    alembic.parm( 'fileName' ).set( '$HIP/geo/' + name + ".abc" )
                    alembic.parm( 'reload' ).pressButton()

                    '''
                    vraypoxy = geo.node( 'vrayproxy' )
                    if vraypoxy == None:
                        vraypoxy = geo.createNode('VRayNodeVRayProxy')
                        vraypoxy.moveToGoodPosition()
                    vraypoxy.parm('file').set('$HIP/geo/' + name + ".abc")
                    vraypoxy.parm('loadtype').set(2)
                    vraypoxy.parm('reload').pressButton()
                    vraypoxy.parm('scale').set(0.01)
                    vraypoxy.parm('flip_axis').set(1)                    
                    
                    unpack = geo.node( 'unpack1' )
                    if unpack == None:
                        unpack = vraypoxy.createOutputNode('unpack')
                    '''

                    '''
                    convert = geo.node( 'convert1' )
                    if convert == None:
                        convert = alembic.createOutputNode( 'convert' )
                        #convert = unpack.createOutputNode('convert')
                    '''

                    xform = geo.node( 'xform1' )
                    if xform == None:
                        #xform = convert.createOutputNode('xform')
                        xform = alembic.createOutputNode('xform', 'xform1')
                    xform.parm('scale').set(0.01)

                    properties = geo.node( 'properties' )
                    if properties == None:
                        #properties = convert.createOutputNode( 'attribwrangle', 'properties' )
                        properties = xform.createOutputNode('attribwrangle', 'properties')
                        properties.parm( 'class' ).set( 0 )
                        properties.setDisplayFlag(True)
                        #properties.setRenderFlag(True)
                    properties.parm( 'snippet' ).set( 'v@wirecolor = set(' + str( wirecolor[0] ) + ', ' + str( wirecolor[1] ) + ', ' + str( wirecolor[2] ) + ');\ni@handle = ' + str( handle ) + ';' )

                    vraypoxy = geo.node('vrayproxy1')
                    if vraypoxy == None:
                        vraypoxy = geo.createNode('VRayNodeVRayProxy', 'vrayproxy1')
                        vraypoxy.moveToGoodPosition()
                    #vraypoxy.parm('file').set('$HIP/geo/' + name + ".abc")
                    vraypoxy.parm('file').setExpression('`chs("../alembic1/fileName")`')
                    vraypoxy.parm('reload').pressButton()
                    #vraypoxy.parm('scale').set(0.01)
                    vraypoxy.parm('scale').setExpression('ch("../xform1/scale")')
                    vraypoxy.moveToGoodPosition()
                    vraypoxy.setRenderFlag(True)

            else:
                    print( 'cannot import ' + name + ', cannot access temporary .abc file' )

    print('object(s) sucessfully imported')

    addSceneWirecolorVisualizer()

else:
    print( 'cannot import object from clipboad, wrong type!' )

