#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#
#       This file is part of the E-Cell System
#
#       Copyright (C) 1996-2007 Keio University
#       Copyright (C) 2005-2007 The Molecular Sciences Institute
#
#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#
#
# E-Cell System is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
# 
# E-Cell System is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public
# License along with E-Cell System -- see the file COPYING.
# If not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# 
#END_HEADER

from weakref import ref, WeakKeyDictionary
import gtk

try:
    import gnomecanvas as gnomecanvas
except:
    import gnome.canvas as gnomecanvas

import ecell.ui.model_editor.canvas as base

__all__ = (
    'CanvasWidgetWrapper',
    )

class CanvasWidgetWrapper( base.CanvasWidgetWrapper ):
    def __init__( self, antialias = True ):
        self.native = gnomecanvas.Canvas( aa = antialias )
        self.canvas = Canvas( self, self.native.root() )
        self.nativeToWrapperMap = WeakKeyDictionary()

    def getBounds( self ):
        bounds = self.native.root().get_bounds()
        return ( bounds[ 0 ], bounds[ 1 ],
            bounds[ 2 ] - bounds[ 0 ], bounds[ 3 ] - bounds[ 1 ] )

    def convertCoordToPixels( self, coord ):
        return self.native.w2c( *coord )

    def convertSizeToPixels( self, size ):
        r = self.native.w2c( size[ 0 ], size[ 1 ] )
        o = self.native.w2c( 0, 0 )
        return ( r[ 0 ] - o[ 0 ], r[ 1 ] - o[ 1 ] )

    def convertCoordToLogical( self, coord ):
        return self.native.c2w( *coord )

    def convertSizeToLogical( self, size ):
        r = self.native.c2w( size[ 0 ], size[ 1 ] )
        o = self.native.c2w( 0, 0 )
        return ( r[ 0 ] - o[ 0 ], r[ 1 ] - o[ 1 ] )

    def setCanvasSize( self, size ):
        self.native.set_scroll_region( 0, 0, size[ 0 ], size[ 1 ] )
        self.native.size_allocate( gtk.gdk.Rectangle(
            0, 0, *self.convertSizeToPixels( size ) ) )

    def getCanvasSize( self ):
        bounds = self.native.get_scroll_region()
        return ( bounds[ 2 ] - bounds[ 0 ], bounds[ 3 ] - bounds[ 1 ] )

    def getItemAt( self, coord ):
        native = self.native.get_item_at( *coord )
        if native == None:
            return None
        return self.nativeToWrapperMap[ native ]

def fromGdkEvent( source, e ):
    if e.type == gtk.gdk.BUTTON_PRESS:
        retval = base.MouseEvent(
            'pressed', source,
            time = e.time,
            button = e.button,
            pos = source.convertCoordToItem( e.get_coords() ),
            root = e.get_root_coords() )
    elif e.type == gtk.gdk.BUTTON_RELEASE:
        retval = base.MouseEvent( 'released', source,
            time = e.time,
            button = e.button,
            pos = source.convertCoordToItem( e.get_coords() ),
            root = e.get_root_coords() )
    elif e.type == gtk.gdk.MOTION_NOTIFY:
        retval = base.MouseEvent( 'moved', source,
            time = e.time,
            pos = source.convertCoordToItem( e.get_coords() ),
            root = e.get_root_coords() )
    elif e.type == gtk.gdk.ENTER_NOTIFY:
        retval = base.MouseEvent( 'entered', source,
            pos = source.convertCoordToItem( e.get_coords() ),
            root = e.get_root_coords() )
    elif e.type == gtk.gdk.LEAVE_NOTIFY:
        retval = base.MouseEvent( 'left', source,
            time = e.time,
            pos = source.convertCoordToItem( e.get_coords() ),
            root = e.get_root_coords() )
    elif e.type == gtk.gdk._2BUTTON_PRESS:
        retval = base.MouseEvent(
            'double_clicked', source,
            time = e.time,
            button = e.button,
            pos = source.convertCoordToItem( e.get_coords() ),
            root = e.get_root_coords() )
    elif e.type == gtk.gdk._3BUTTON_PRESS:
        retval = base.MouseEvent(
            'triple_clicked', source,
            time = e.time,
            button = e.button,
            pos = source.convertCoordToItem( e.get_coords() ),
            root = e.get_root_coords() )
    else:
        raise RuntimeError, "Fix me!"
    return retval

class CanvasItemImpl( object ):
    __slots__ = (
        'native',
        'wrapper',
        'transform'
        )

    GRAB_CURSOR_EVENT_MASK = \
        gtk.gdk.POINTER_MOTION_MASK \
        | gtk.gdk.BUTTON_MOTION_MASK \
        | gtk.gdk.BUTTON_PRESS_MASK \
        | gtk.gdk.BUTTON_RELEASE_MASK \
        | gtk.gdk.ENTER_NOTIFY_MASK \
        | gtk.gdk.LEAVE_NOTIFY_MASK

    def __init__( self, wrapper, native, **params ):
        self.wrapper = wrapper
        self.native = native
        for key, val in params.iteritems():
            CanvasItemImpl.__setattr__( self, key, val )

    def __del__( self ):
        self.native.destroy()

    def __setattr__( self, key, val ):
        if key == 'parent':
            val = ref( val )
        elif key == 'transform':
            self.native.affine_absolute( val )
        return object.__setattr__( self, key, val )

    def __getattribute__( self, key ):
        if key == 'bounds':
            return self.native.get_bounds()
        val = object.__getattribute__( self, key )
        if isinstance( val, ref ):
            return val()
        else:
            return val

    def addObserver( self, type, observer ):
        self.native.connect(
            'event',
            lambda o, e: observer( fromGdkEvent( self, e ) ) )

    def upper( self, another ):
        anothersZOrder = self.parent.itemToZOrderMap[ another ]
        myZOrder = self.parent.itemToZOrderMap[ self ]
        if anothersZOrder > myZOrder:
            self.native.raise_( anothersZOrder - myZOrder )
            for item, zOrder in self.parent.itemToZOrderMap.iteritems():
                if zOrder > myZOrder and zOrder <= anothersZOrder:
                    self.parent.itemToZOrderMap[ item ] -= 1
            self.parent.itemToZOrderMap[ self ] = anothersZOrder

    def lower( self, another ):
        anothersZOrder = self.parent.itemToZOrderMap[ another ]
        myZOrder = self.parent.itemToZOrderMap[ self ]
        if anothersZOrder < myZOrder:
            self.native.lower( myZOrder - anothersZOrder )
        for item, zOrder in self.parent.itemToZOrderMap.iteritems():
            if zOrder > myZOrder and zOrder <= anothersZOrder:
                self.parent.itemToZOrderMap[ item ] += 1
            self.parent.itemToZOrderMap[ self ] = anothersZOrder

    def update( self ):
        # XXX: mimics gnome.CanvasItem.request_update()
        # which is not exposed as Python API on wrong purpose...
        parent = self.native.get_property( 'parent' )
        if parent:
            self.native.reparent( parent )
        else:
            self.wrapper.native.update_now()

    def convertCoordToWorld( self, coord ):
        return self.native.i2w( *coord )

    def convertSizeToWorld( self, size ):
        r = self.native.i2w( size[ 0 ], size[ 1 ] )
        o = self.native.i2w( 0, 0 )
        return ( r[ 0 ] - o[ 0 ], r[ 1 ] - o[ 1 ] )

    def convertCoordToItem( self, coord ):
        return self.native.w2i( *coord )

    def convertSizeToItem( self, size ):
        r = self.native.w2i( size[ 0 ], size[ 1 ] )
        o = self.native.w2i( 0, 0 )
        return ( r[ 0 ] - o[ 0 ], r[ 1 ] - o[ 1 ] )

    def grabCursor( self, cause, cursor = None ):
        return self.native.grab( self.GRAB_CURSOR_EVENT_MASK,
            cursor, long( cause.time ) )

    def ungrabCursor( self, cause ):
        return self.native.ungrab( long( cause.time ) )

    def dispose( self ):
        zOrder = self.parent.itemToZOrderMap[ self ]
        del self.parent.zOrderToItemMap[ zOrder ]
        del self.parent.itemToZOrderMap[ self ]
        del self.wrapper.nativeToWrapperMap[ self.native ]
        for i in range( zOrder, len( self.parent.zOrderToItemMap ) ):
            self.parent.itemToZOrderMap[ self.parent.zOrderToItemMap[ i ] ] = i

class BezierPath( CanvasItemImpl, base.BezierPath ):
    def __setattr__( self, key, val ):
        CanvasItemImpl.__setattr__( self, key, val )
        if key == 'strokeColor':
            self.native.set_property( 'outline_color_rgba', val )
        elif key == 'fillColor':
            self.native.set_property( 'fill_color_rgba', val )
        elif key == 'strokeWidth':
            self.native.set_property( 'width_units', val )
        elif key == 'path':
            self.native.set_property( 'bpath',
                createPathObject( val ) )

class Polygon( CanvasItemImpl, base.Polygon ):
    def __setattr__( self, key, val ):
        CanvasItemImpl.__setattr__( self, key, val )
        if key == 'strokeColor':
            self.native.set_property( 'outline_color_rgba', val )
        elif key == 'fillColor':
            self.native.set_property( 'fill_color_rgba', val )
        elif key == 'strokeWidth':
            self.native.set_property( 'width_units', val )
        elif key == 'points':
            self.native.set_property( 'points',
                sum( val, (), ) )

class Polyline( CanvasItemImpl, base.Polyline ):
    def __setattr__( self, key, val ):
        CanvasItemImpl.__setattr__( self, key, val )
        if key == 'color':
            self.native.set_property( 'fill_color_rgba', val )
        elif key == 'width':
            self.native.set_property( 'width_units', val )
        elif key == 'points':
            self.native.set_property( 'points', sum( val, (), ) )
        elif key == 'arrowSpec':
            self.native.set_property( 'arrow_shape_a', val[ 'tipLength' ] * self.width )
            self.native.set_property( 'arrow_shape_b', val[ 'length' ] * self.width )
            self.native.set_property( 'arrow_shape_c', val[ 'width' ] * self.width / 2 )
        elif key == 'startArrow':
            self.native.set_property( 'first-arrowhead', val )
        elif key == 'endArrow':
            self.native.set_property( 'last-arrowhead', val )

class Rectangle( CanvasItemImpl, base.Rectangle ):
    def __setattr__( self, key, val ):
        CanvasItemImpl.__setattr__( self, key, val )
        if key == 'strokeColor':
            self.native.set_property( 'outline_color_rgba', val )
        elif key == 'fillColor':
            self.native.set_property( 'fill_color_rgba', val )
        elif key == 'strokeWidth':
            self.native.set_property( 'width_units', val )
        elif key == 'width':
            self.native.set_property( 'x2', self.x + val )
        elif key == 'height':
            self.native.set_property( 'y2', self.y + val )
        elif key == 'x':
            self.native.set_property( 'x1', val )
        elif key == 'y':
            self.native.set_property( 'y1', val )

class Ellipse( CanvasItemImpl, base.Ellipse ):
    def __setattr__( self, key, val ):
        CanvasItemImpl.__setattr__( self, key, val )
        if key == 'strokeColor':
            self.native.set_property( 'outline_color_rgba', val )
        elif key == 'fillColor':
            self.native.set_property( 'fill_color_rgba', val )
        elif key == 'strokeWidth':
            self.native.set_property( 'width_units', val )
        elif key == 'width':
            self.native.set_property( 'x2', self.x + val )
        elif key == 'height':
            self.native.set_property( 'y2', self.y + val )
        elif key == 'x':
            self.native.set_property( 'x1', val )
        elif key == 'y':
            self.native.set_property( 'y1', val )

class Image( CanvasItemImpl, base.Image ):
    def __getattr__( self, key ):
        if key == 'width':
            return self.native.get_property( 'width' )
        elif key == 'height':
            return self.native.get_property( 'height' )
        return CanvasItemImpl.__getattr__( self, key )

    def __setattr__( self, key, val ):
        CanvasItemImpl.__setattr__( self, key, val )
        if key == 'x':
            self.native.set_property( 'x', val )
        elif key == 'y':
            self.native.set_property( 'y', val )
        elif key == 'anchor':
            self.native.set_property( 'anchor', convertAnchorValue( val ) )
        elif key == 'pixbuf':
            self.native.set_property( 'pixbuf', val )

class Text( CanvasItemImpl, base.Text ):
    def __getattr__( self, key ):
        if key == 'width':
            return self.native.get_property( 'text-width' )
        elif key == 'height':
            return self.native.get_property( 'text-height' )
        return CanvasItemImpl.__getattr__( self, key )

    def __setattr__( self, key, val ):
        CanvasItemImpl.__setattr__( self, key, val )
        if key == 'x':
            self.native.set_property( 'x', val )
        elif key == 'y':
            self.native.set_property( 'y', val )
        elif key == 'anchor':
            self.native.set_property( 'anchor', convertAnchorValue( val ) )
        elif key == 'color':
            self.native.set_property( 'fill_color_rgba', val )
        elif key == 'font':
            self.native.set_property( 'font', val )
        elif key == 'text':
            self.native.set_property( 'text', val )

def createPathObject( path ):
    repr = []
    last_pos = ( 0, 0 )
    for item in path:
        if item[ 0 ] == base.MOVE_TO:
            if item[ 1 ]:
                pos = (
                    last_pos[ 0 ] + item[ 2 ],
                    last_pos[ 1 ] + item[ 3 ]
                    )
            else:
                pos = item[ 2: 4 ]
            repr.append( (
                gnomecanvas.MOVETO, pos[ 0 ], pos[ 1 ]
                ) )
            last_pos = pos
        elif item[ 0 ] == base.LINE_TO:
            if item[ 1 ]:
                pos = (
                    last_pos[ 0 ] + item[ 2 ],
                    last_pos[ 1 ] + item[ 3 ]
                    )
            else:
                pos = item[ 2: 4 ]
            repr.append( (
                gnomecanvas.LINETO, pos[ 0 ], pos[ 1 ]
                ) )
            last_pos = pos
        elif item[ 0 ] == base.CURVE_TO:
            if len( item ) >= 6:
                cp = item[ 6: ]
            else:
                cp = item[ 4: ]
            if item[ 1 ]:
                pos = (
                    last_pos[ 0 ] + item[ 2 ],
                    last_pos[ 1 ] + item[ 3 ]
                    )
                repr.append( (
                    gnomecanvas.CURVETO,
                    last_pos[ 0 ] + item[ 4 ], last_pos[ 1 ] + item[ 5 ],
                    last_pos[ 0 ] + cp[ 0 ], last_pos[ 1 ] + cp[ 1 ],
                    pos[ 0 ], pos[ 1 ]
                    ) )
            else:
                pos = item[ 2: 4 ]
                repr.append( (
                    gnomecanvas.CURVETO,
                    item[ 4 ], item[ 5 ],
                    cp[ 0 ], cp[ 1 ],
                    pos[ 0 ], pos[ 1 ]
                    ) )
            last_pos = pos
        elif item[ 0 ] == base.CLOSE:
            repr.append( ( gnomecanvas.END, ) )
    return gnomecanvas.path_def_new( repr )

anchor_map = {
    base.ANCHOR_CENTER     : gtk.ANCHOR_CENTER,
    base.ANCHOR_NORTH      : gtk.ANCHOR_NORTH,
    base.ANCHOR_NORTH_WEST : gtk.ANCHOR_NORTH_WEST,
    base.ANCHOR_NORTH_EAST : gtk.ANCHOR_NORTH_EAST,
    base.ANCHOR_SOUTH      : gtk.ANCHOR_SOUTH,
    base.ANCHOR_SOUTH_WEST : gtk.ANCHOR_SOUTH_WEST,
    base.ANCHOR_SOUTH_EAST : gtk.ANCHOR_SOUTH_EAST,
    base.ANCHOR_WEST       : gtk.ANCHOR_WEST,
    base.ANCHOR_EAST       : gtk.ANCHOR_EAST
}

def convertAnchorValue( value ):
    return anchor_map[ value ]

class Canvas( CanvasItemImpl, base.Canvas ):
    __slots__ = (
        'itemToZOrderMap',
        'zOrderToItemMap'
        )

    def __init__( self, wrapper, native, **params ):
        CanvasItemImpl.__init__( self, wrapper, native, **params )
        self.itemToZOrderMap = {}
        self.zOrderToItemMap = []

    def __setattr__( self, key, val ):
        CanvasItemImpl.__setattr__( self, key, val )
        if key == 'x':
            self.native.set_property( 'x', val )
        elif key == 'y':
            self.native.set_property( 'y', val )

    def drawBezierPath( self, strokeColor, fillColor, strokeWidth, path ):
        bp = self.native.add( gnomecanvas.CanvasBpath,
                outline_color_rgba = strokeColor,
                fill_color_rgba = fillColor,
                bpath = createPathObject( path ),
                width_units = strokeWidth )
        obj = BezierPath( self.wrapper, bp, parent = self,
            strokeColor = strokeColor, fillColor = fillColor,
            strokeWidth = strokeWidth, path = path )
        self.itemToZOrderMap[ obj ] = len( self.zOrderToItemMap )
        self.zOrderToItemMap.append( obj )
        self.wrapper.nativeToWrapperMap[ bp ] = obj
        return obj

    def drawPolyline( self, color, width, startArrow, endArrow, arrowSpec, points ):
        pline = self.native.add( gnomecanvas.CanvasLine,
            fill_color_rgba = color,
            points = sum( points, () ),
            width_units = width,
            first_arrowhead = startArrow, last_arrowhead = endArrow )
        if arrowSpec != None:
            pline.set_property( 'arrow_shape_a', arrowSpec[ 'tipLength' ] * width )
            pline.set_property( 'arrow_shape_b', arrowSpec[ 'length' ] * width )
            pline.set_property( 'arrow_shape_c', arrowSpec[ 'width' ] * width / 2 )
        obj = Polyline( self.wrapper, pline, parent = self,
            color = color, points = points,
            width = width, startArrow = startArrow, endArrow = endArrow,
            arrowSpec = arrowSpec )
        self.itemToZOrderMap[ obj ] = len( self.zOrderToItemMap )
        self.zOrderToItemMap.append( obj )
        self.wrapper.nativeToWrapperMap[ pline ] = obj
        return obj

    def drawPolygon( self, strokeColor, fillColor, strokeWidth, points ):
        poly = self.native.add( gnomecanvas.CanvasPolygon,
            outline_color_rgba = strokeColor,
            fill_color_rgba = fillColor,
            points = sum( points, () ),
            width_units = strokeWidth )
        obj = Polygon( self.wrapper, poly, parent = self,
            strokeColor = strokeColor, fillColor = fillColor,
            points = points )
        self.itemToZOrderMap[ obj ] = len( self.zOrderToItemMap )
        self.zOrderToItemMap.append( obj )
        self.wrapper.nativeToWrapperMap[ poly ] = obj
        return obj

    def drawRectangle( self, x, y, width, height, strokeColor, fillColor, strokeWidth ):
        rect = self.native.add( gnomecanvas.CanvasRect,
            outline_color_rgba = strokeColor,
            fill_color_rgba = fillColor,
            x1 = x, y1 = y, x2 = x + width, y2 = y + height,
            width_units = strokeWidth )
        obj = Rectangle( self.wrapper, rect, parent = self,
            strokeColor = strokeColor, fillColor = fillColor,
            x = x, y = y, width = width, height = height )
        self.itemToZOrderMap[ obj ] = len( self.zOrderToItemMap )
        self.zOrderToItemMap.append( obj )
        self.wrapper.nativeToWrapperMap[ rect ] = obj
        return obj

    def drawEllipse( self, x, y, width, height, strokeColor, fillColor, strokeWidth ):
        ell = self.native.add( gnomecanvas.CanvasEllipse,
            outline_color_rgba = strokeColor,
            fill_color_rgba = fillColor,
            x1 = x, y1 = y, x2 = x + width, y2 = y + height,
            width_units = strokeWidth )
        obj = Ellipse( self.wrapper, ell, parent = self,
            x = x, y = y, width = width, height = height,
            strokeColor = strokeColor, fillColor = fillColor,
            strokeWidth = strokeWidth )
        self.itemToZOrderMap[ obj ] = len( self.zOrderToItemMap )
        self.zOrderToItemMap.append( obj )
        self.wrapper.nativeToWrapperMap[ ell ] = obj
        return obj

    def drawText( self, x, y, color, anchor, font, text ):
        txt = self.native.add( gnomecanvas.CanvasText,
                x = x, y = y, fill_color_rgba = color,
                anchor = convertAnchorValue( anchor ),
                font = font, text = text )
        obj = Text( self.wrapper, txt, parent = self,
            x = x, y = y, color = color, anchor = anchor,
            font = font, text = text )
        self.itemToZOrderMap[ obj ] = len( self.zOrderToItemMap )
        self.zOrderToItemMap.append( obj )
        self.wrapper.nativeToWrapperMap[ txt ] = obj
        return obj

    def drawImage( self, x, y, anchor, pixbuf ):
        image = self.native.add( gnomecanvas.CanvasPixbuf,
                x = x, y = y, anchor = convertAnchorValue( anchor ),
                width = pixbuf.width, height = pixbuf.height,
                widget = widget )
        obj = Image( self.wrapper, image, parent = self,
            x = x, y = y,
            anchor = anchor, pixbuf = pixbuf )
        self.itemToZOrderMap[ obj ] = len( self.zOrderToItemMap )
        self.zOrderToItemMap.append( obj )
        self.wrapper.nativeToWrapperMap[ image ] = obj
        return obj

    def createChild( self, x, y ):
        canvas = self.native.add( gnomecanvas.CanvasGroup,
                x = x, y = y ) 
        obj = Canvas( self.wrapper, canvas, parent = self, x = x, y = y )
        self.itemToZOrderMap[ obj ] = len( self.zOrderToItemMap )
        self.zOrderToItemMap.append( obj )
        self.wrapper.nativeToWrapperMap[ canvas ] = obj
        return obj
