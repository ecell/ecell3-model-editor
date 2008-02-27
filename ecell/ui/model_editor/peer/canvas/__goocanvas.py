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
import operator as oper
import gtk
import pango
import cairo

import goocanvas

import ecell.ui.model_editor.canvas as base

__all__ = (
    'CanvasWidgetWrapper',
    )

class CanvasWidgetWrapper( object ):
    def __init__( self ):
        self.native = goocanvas.Canvas()
        self.canvas = Canvas( self, self.native.get_root_item() )
        self.nativeToWrapperMap = WeakKeyDictionary()

    def getBounds( self ):
        bounds = self.native.get_root_item().get_bounds()
        return ( bounds.x1, bounds.y1,
            bounds.x2 - bounds.x1, bounds.y2 - bounds.y1 ) 

    def convertCoordToPixels( self, coord ):
        return map( int, self.native.convert_to_pixels( *coord ) )

    def convertSizeToPixels( self, size ):
        r = self.native.convert_to_pixels( size[ 0 ], size[ 1 ] )
        o = self.native.convert_to_pixels( 0, 0 )
        return ( int( r[ 0 ] - o[ 0 ] ), int ( r[ 1 ] - o[ 1 ] ) )

    def convertCoordToLogical( self, coord ):
        return self.native.convert_from_pixels( *coord )

    def convertSizeToLogical( self, size ):
        r = self.native.convert_from_pixels( size[ 0 ], size[ 1 ] )
        o = self.native.convert_from_pixels( 0, 0 )
        return ( r[ 0 ] - o[ 0 ], r[ 1 ] - o[ 1 ] )

    def setCanvasSize( self, size ):
        self.native.set_bounds( 0, 0, size[ 0 ], size [ 1 ] )
        self.native.size_allocate( gtk.gdk.Rectangle(
            0, 0, *self.convertSizeToPixels( size ) ) )

    def getCanvasSize( self ):
        bounds = self.native.get_bounds()
        lt = self.native.convert_to_pixels( bounds[ 0 ], bounds[ 1 ] )
        rb = self.native.convert_to_pixels( bounds[ 2 ], bounds[ 3 ] )
        return ( rb[ 0 ] - lt[ 0 ], rb[ 1 ] - lt[ 1 ] )

    def getItemAt( self,  coords ):
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
            pos = e.get_coords(),
            root = map( oper.add,
                source.wrapper.native.window.get_origin(),
                source.wrapper.convertCoordToPixels( e.get_root_coords() ) )
            )
    elif e.type == gtk.gdk.BUTTON_RELEASE:
        retval = base.MouseEvent( 'released', source,
            time = e.time,
            button = e.button,
            pos = e.get_coords(),
            root = map( oper.add,
                source.wrapper.native.window.get_origin(),
                source.wrapper.convertCoordToPixels( e.get_root_coords() ) )
            )
    elif e.type == gtk.gdk.MOTION_NOTIFY:
        retval = base.MouseEvent( 'moved', source,
            time = e.time,
            pos = e.get_coords(),
            root = map( oper.add,
                source.wrapper.native.window.get_origin(),
                source.wrapper.convertCoordToPixels( e.get_root_coords() ) )
            )
    elif e.type == gtk.gdk.ENTER_NOTIFY:
        retval = base.MouseEvent( 'entered', source,
            time = e.time,
            pos = e.get_coords(),
            root = map( oper.add,
                source.wrapper.native.window.get_origin(),
                source.wrapper.convertCoordToPixels( e.get_root_coords() ) )
            )
    elif e.type == gtk.gdk.LEAVE_NOTIFY:
        retval = base.MouseEvent( 'left', source,
            time = e.time,
            pos = e.get_coords(),
            root = map( oper.add,
                source.wrapper.native.window.get_origin(),
                source.wrapper.convertCoordToPixels( e.get_root_coords() ) )
            )
    elif e.type == gtk.gdk._2BUTTON_PRESS:
        retval = base.MouseEvent(
            'double_clicked', source,
            time = e.time,
            button = e.button,
            pos = e.get_coords(),
            root = map( oper.add,
                source.wrapper.native.window.get_origin(),
                source.wrapper.convertCoordToPixels( e.get_root_coords() ) )
            )
    elif e.type == gtk.gdk._3BUTTON_PRESS:
        retval = base.MouseEvent(
            'triple_clicked', source,
            time = e.time,
            button = e.button,
            pos = e.get_coords(), 
            root = map( oper.add,
                source.wrapper.native.window.get_origin(),
                source.wrapper.convertCoordToPixels( e.get_root_coords() ) )
            )
    else:
        raise RuntimeError, "Fix me!"
    return retval

class CanvasItemImpl( object ):
    __slots__ = (
        'native',
        'wrapper'
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

    def __setattr__( self, key, val ):
        if key == 'parent':
            val = ref( val )
        elif key == 'transform':
            self.native.set_transform( cairo.Matrix( *val ) )
        return object.__setattr__( self, key, val )

    def __getattribute__( self, key ):
        if key == 'bounds':
            b = self.native.get_bounds()
            return ( b.x1, b.y1, b.x2, b.y2 )

        val = object.__getattribute__( self, key )
        if isinstance( val, ref ):
            return val()
        else:
            return val

    def __del__( self ):
        self.native.remove()

    def addObserver( self, type, observer ):
        if type == base.CanvasEvent or issubclass( type, base.MouseEvent ):
            decorated = lambda o, n, e: observer( fromGdkEvent( self, e ) )
            self.native.connect( 'motion_notify_event', decorated )
            self.native.connect( 'enter_notify_event', decorated )
            self.native.connect( 'leave_notify_event', decorated )
            self.native.connect( 'button_press_event', decorated )
            self.native.connect( 'button_release_event', decorated )

    def upper( self, another ):
        self.native.raise_( another.native )

    def lower( self, another ):
        self.native.lower( another.native )

    def update( self ):
        self.native.request_update()

    def convertCoordToWorld( self, coord ):
        return self.wrapper.native.convert_from_item_space(
            self.native, *coord )

    def convertSizeToWorld( self, size ):
        r = self.wrapper.native.convert_from_item_space( size[ 0 ], size[ 1 ] )
        o = self.wrapper.native.convert_from_item_space( 0, 0 )
        return ( r[ 0 ] - o[ 0 ], r[ 1 ] - o[ 1 ] )

    def convertCoordToItem( self, coord ):
        return self.wrapper.native.convert_to_item_space(
            self.native, *coord )

    def convertSizeToItem( self, size ):
        r = self.wrapper.native.convert_to_item_space( size[ 0 ], size[ 1 ] )
        o = self.wrapper.native.convert_to_item_space( 0, 0 )
        return ( r[ 0 ] - o[ 0 ], r[ 1 ] - o[ 1 ] )

    def grabCursor( self, cause, cursor = None ):
        self.wrapper.native.pointer_grab( self.native,
            self.GRAB_CURSOR_EVENT_MASK,
            cursor, cause.time )

    def ungrabCursor( self, cause ):
        self.wrapper.native.pointer_ungrab( self.native, cause.time )

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
            if val == None:
                self.native.get_style().set_style_property( 'GooCanvasStyle:stroke_pattern', None )
            else:
                self.native.set_property( 'stroke_color_rgba', val )
        elif key == 'fillColor':
            if val == None:
                self.native.get_style().set_style_property( 'GooCanvasStyle:fill_pattern', None )
            else:
                self.native.set_property( 'fill_color_rgba', val )
        elif key == 'strokeWidth':
            self.native.set_property( 'line_width', val )
        elif key == 'path':
            self.native.set_property( 'data', createPathData( val ) )

class Polygon( CanvasItemImpl, base.Polygon ):
    def __setattr__( self, key, val ):
        CanvasItemImpl.__setattr__( self, key, val )
        if key == 'strokeColor':
            if val == None:
                self.native.get_style().set_style_property( 'GooCanvasStyle:stroke_pattern', None )
            else:
                self.native.set_property( 'stroke_color_rgba', val )
        elif key == 'fillColor':
            if val == None:
                self.native.get_style().set_style_property( 'GooCanvasStyle:fill_pattern', None )
            else:
                self.native.set_property( 'fill_color_rgba', val )
        elif key == 'strokeWidth':
            self.native.set_property( 'line_width', val )
        elif key == 'points':
            self.native.set_property( 'points',
                goocanvas.Points(
                    isinstance( val, list ) and val or list( val ) ) )

class Polyline( CanvasItemImpl, base.Polyline ):
    def __setattr__( self, key, val ):
        CanvasItemImpl.__setattr__( self, key, val )
        if key == 'color':
            if val == None:
                self.native.get_style().set_style_property( 'GooCanvasStyle:stroke_pattern', None )
            else:
                self.native.set_property( 'stroke_color_rgba', val )
        elif key == 'width':
            self.native.set_property( 'line_width', val )
        elif key == 'points':
            self.native.set_property( 'points',
                goocanvas.Points(
                    isinstance( val, list ) and val or list( val ) ) )
        elif key == 'arrowSpec':
            self.native.set_property( 'arrow_length', val[ 'length' ] )
            self.native.set_property( 'arrow_tip_length', val[ 'tipLength' ] )
            self.native.set_property( 'arrow_width', val[ 'width' ] )
        elif key == 'startArrow':
            self.native.set_property( 'start_arrow', val )
        elif key == 'endArrow':
            self.native.set_property( 'end_arrow', val )

class Rectangle( CanvasItemImpl, base.Rectangle ):
    def __setattr__( self, key, val ):
        CanvasItemImpl.__setattr__( self, key, val )
        if key == 'strokeColor':
            if val == None:
                self.native.get_style().set_style_property( 'GooCanvasStyle:stroke_pattern', None )
            else:
                self.native.set_property( 'stroke_color_rgba', val )
        elif key == 'fillColor':
            if val == None:
                self.native.get_style().set_style_property( 'GooCanvasStyle:fill_pattern', None )
            else:
                self.native.set_property( 'fill_color_rgba', val )
        elif key == 'strokeWidth':
            self.native.set_property( 'line_width', val )
        elif key == 'width':
            self.native.set_property( 'width', val )
        elif key == 'height':
            self.native.set_property( 'height', val )
        elif key == 'x':
            self.native.set_property( 'x', val )
        elif key == 'y':
            self.native.set_property( 'y', val )

class Ellipse( CanvasItemImpl, base.Ellipse ):
    def __setattr__( self, key, val ):
        CanvasItemImpl.__setattr__( self, key, val )
        if key == 'strokeColor':
            if val == None:
                self.native.get_style().set_style_property( 'GooCanvasStyle:stroke_pattern', None )
            else:
                self.native.set_property( 'stroke_color_rgba', val )
        elif key == 'fillColor':
            if val == None:
                self.native.get_style().set_style_property( 'GooCanvasStyle:fill_pattern', None )
            else:
                self.native.set_property( 'fill_color_rgba', val )
        elif key == 'strokeWidth':
            self.native.set_property( 'line_width', val )
        elif key == 'width':
            self.native.set_property( 'radius_x', val / 2 )
        elif key == 'height':
            self.native.set_property( 'radius_y', val / 2 )
        elif key == 'x':
            self.native.set_property( 'center_x', val + self.width / 2 )
        elif key == 'y':
            self.native.set_property( 'center_y', val + self.height / 2 )

class Image( CanvasItemImpl, base.Ellipse ):
    def __getattr__( self, key ):
        if key == 'width':
            return self.native.get_property( 'width' )
        elif key == 'height':
            return self.native.get_property( 'height' )

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
    def __init__( self, wrapper, native, **params ):
        CanvasItemImpl.__init__( self, wrapper, native, **params )
        l = pango.Layout( gtk.gdk.pango_context_get() )
        l.set_width( -1 )
        l.set_text( params[ 'text' ] )
        l.set_font_description( self.native.get_style().get_style_property( 'GooCanvasStyle:font_desc' ) )
        self.layouting = l

    def __getattr__( self, key ):
        if key == 'width':
            phys, logs = self.layouting.get_extents()
            return float( logs[ 2 ] - logs[ 0 ] ) / pango.SCALE
        elif key == 'height':
            phys, logs = self.layouting.get_extents()
            return float( logs[ 3 ] - logs[ 1 ] ) / pango.SCALE

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
            self.layouting.set_font_description( self.native.get_style().get_style_property( 'GooCanvasStyle:font_desc' ) )
        elif key == 'text':
            self.native.set_property( 'text', val )
            self.layouting.set_text( val )

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

def createPathData( path ):
    repr = ''
    for item in path:
        if item[ 0 ] == base.MOVE_TO:
            if item[ 1 ]:
                repr += 'm %f,%f ' % tuple( item[ 2: 4 ] )
            else:
                repr += 'M %f,%f ' % tuple( item[ 2: 4 ] )
        elif item[ 0 ] == base.LINE_TO:
            if item[ 1 ]:
                repr += 'l %f,%f ' % tuple( item[ 2: 4 ] )
            else:
                repr += 'L %f,%f ' % tuple( item[ 2: 4 ] )
        elif item[ 0 ] == base.CURVE_TO:
            if len( item ) >= 6:
                if item[ 1 ]:
                    repr += 'c %f,%f %f,%f %f,%f ' % tuple(
                        item[ 4: 8 ] + item[ 2: 4 ] )
                else:
                    repr += 'c %f,%f %f,%f %f,%f ' % tuple(
                        item[ 4: 8 ] + item[ 2: 4 ] )
            else:
                if item[ 1 ]:
                    repr += 's %f,%f %f,%f ' % tuple(
                        item[ 4: 6 ] + item[ 2: 4 ] )
                else:
                    repr += 'S %f,%f %f,%f ' % tuple(
                        item[ 4: 6 ] + item[ 2: 4 ] )
        elif item[ 0 ] == base.CLOSE:
            repr += 'z '
    return repr

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
        if key == 'x' or key == 'y':
            mat = self.native.get_transform()
            if mat:
                mat = cairo.Matrix( mat[ 0 ], mat[ 1 ], mat[ 2 ], mat[ 3 ], self.x, self.y )
            else:
                mat = cairo.Matrix( 1, 0, 0, 1, x, y )
            self.native.set_transform( mat )

    def drawBezierPath( self, strokeColor, fillColor, strokeWidth, path ):
        bp = goocanvas.Path( parent = self.native,
                data = createPathData( path ),
                line_width = strokeWidth )
        if strokeColor == None:
            bp.get_style().set_style_property( 'GooCanvasStyle:stroke_pattern', None )
        else:
            bp.set_property( 'stroke_color_rgba', strokeColor )
        if fillColor == None:
            bp.get_style().set_style_property( 'GooCanvasStyle:fill_pattern', None )
        else:
            bp.set_property( 'fill_color_rgba', fillColor )
        obj = BezierPath( self.wrapper, bp, parent = self,
            strokeColor = strokeColor,
            fillColor = fillColor,
            strokeWidth = strokeWidth,
            path = path )
        self.itemToZOrderMap[ obj ] = len( self.zOrderToItemMap )
        self.zOrderToItemMap.append( obj )
        self.wrapper.nativeToWrapperMap[ bp ] = obj
        return obj

    def drawPolyline( self, color, width, startArrow, endArrow, arrowSpec, points ):
        poly = goocanvas.Polyline( parent = self.native,
            close_path = False,
            points = goocanvas.Points(
                isinstance( points, list ) and points or list( points ) ),
            line_width = width, start_arrow = startArrow,
            end_arrow = endArrow )
        if color == None:
            poly.get_style().set_style_property( 'GooCanvasStyle:stroke_pattern', None )
        else:
            poly.set_property( 'stroke_color_rgba', color )
        if arrowSpec != None:
            poly.set_property( 'arrow_length', arrowSpec[ 'length' ] )
            poly.set_property( 'arrow_tip_length', arrowSpec[ 'tipLength' ] )
            poly.set_property( 'arrow_width', arrowSpec[ 'width' ] )
        obj = Polyline( self.wrapper, poly, parent = self,
            color = color, width = width,
            points = points, start_arrow = startArrow, end_arrow = endArrow,
            arrow_spec = arrowSpec )
        self.itemToZOrderMap[ obj ] = len( self.zOrderToItemMap )
        self.zOrderToItemMap.append( obj )
        self.wrapper.nativeToWrapperMap[ poly ] = obj
        return obj

    def drawPolygon( self, strokeColor, fillColor, strokeWidth, points ):
        poly = goocanvas.Polyline( parent = self.native,
            close_path = True,
            points = goocanvas.Points(
                isinstance( points, list ) and points or list( points ) ),
            line_width = strokeWidth )
        if strokeColor == None:
            poly.get_style().set_style_property( 'GooCanvasStyle:stroke_pattern', None )
        else:
            poly.set_property( 'stroke_color_rgba', strokeColor )
        if fillColor == None:
            poly.get_style().set_style_property( 'GooCanvasStyle:fill_pattern', None )
        else:
            poly.set_property( 'fill_color_rgba', fillColor )
        obj = Polygon( self.wrapper, poly, parent = self,
            strokeColor = strokeColor, fillColor = fillColor,
            strokeWidth = strokeWidth, points = points )
        self.itemToZOrderMap[ obj ] = len( self.zOrderToItemMap )
        self.zOrderToItemMap.append( obj )
        self.wrapper.nativeToWrapperMap[ poly ] = obj
        return obj

    def drawRectangle( self, x, y, width, height, strokeColor, fillColor, strokeWidth ):
        rect = goocanvas.Rect(
            parent = self.native,
            x = x, y = y, width = width, height = height,
            line_width = strokeWidth )
        if strokeColor == None:
            rect.get_style().set_style_property( 'GooCanvasStyle:stroke_pattern', None )
        else:
            rect.set_property( 'stroke_color_rgba', strokeColor )
        if fillColor == None:
            rect.get_style().set_style_property( 'GooCanvasStyle:fill_pattern', None )
        else:
            rect.set_property( 'fill_color_rgba', fillColor )
        obj = Rectangle( self.wrapper, rect, parent = self,
            x = x, y = y, width = width, height = height,
            strokeColor = strokeColor, fillColor = fillColor,
            strokeWidth = strokeWidth )
        self.itemToZOrderMap[ obj ] = len( self.zOrderToItemMap )
        self.zOrderToItemMap.append( obj )
        self.wrapper.nativeToWrapperMap[ rect ] = obj
        return obj

    def drawEllipse( self, x, y, width, height, strokeColor, fillColor, strokeWidth ):
        rx = width / 2
        ry = height / 2
        ell = goocanvas.Ellipse(
            parent = self.native,
            center_x = x + rx, center_y = y + ry,
            radius_x = rx, radius_y = ry,
            line_width = strokeWidth )
        if strokeColor == None:
            ell.get_style().set_style_property( 'GooCanvasStyle:stroke_pattern', None )
        else:
            ell.set_property( 'stroke_color_rgba', strokeColor )
        if fillColor == None:
            ell.get_style().set_style_property( 'GooCanvasStyle:fill_pattern', None )
        else:
            ell.set_property( 'fill_color_rgba', fillColor )
        obj = Ellipse( self.wrapper, ell, parent = self,
            x = x, y = y, width = width, height = height,
            strokeColor = strokeColor, fillColor = fillColor,
            strokeWidth = strokeWidth )
        self.itemToZOrderMap[ obj ] = len( self.zOrderToItemMap )
        self.zOrderToItemMap.append( obj )
        self.wrapper.nativeToWrapperMap[ ell ] = obj
        return obj

    def drawText( self, x, y, color, anchor, font, text ):
        txt = goocanvas.Text( parent = self.native,
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
        image = self.native.add( goocanvas.Pixbuf,
                x = x, y = y, anchor = convertAnchorValue( anchor ),
                width = pixbuf.width,
                height = pixbuf.height,
                widget = widget )
        obj = Image( self.wrapper, image, parent = self,
            x = x, y = y,
            anchor = anchor, pixbuf = pixbuf )
        self.itemToZOrderMap[ obj ] = len( self.zOrderToItemMap )
        self.zOrderToItemMap.append( obj )
        self.wrapper.nativeToWrapperMap[ image ] = obj
        return obj

    def createChild( self, x, y ):
        child = goocanvas.Group(
            parent = self.native
            )
        mat = child.get_transform()
        if mat:
            mat = cairo.Matrix( mat[ 0 ], mat[ 1 ], mat[ 2 ], mat[ 3 ], x, y )
        else:
            mat = cairo.Matrix( 1, 0, 0, 1, x, y )
        child.set_transform( mat )
        obj = Canvas( self.wrapper, child, x = x, y = y, parent = self )
        self.itemToZOrderMap[ obj ] = len( self.zOrderToItemMap )
        self.zOrderToItemMap.append( obj )
        self.wrapper.nativeToWrapperMap[ child ] = obj
        return obj

