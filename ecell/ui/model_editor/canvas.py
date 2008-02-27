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

ANCHOR_CENTER     = 1
ANCHOR_NORTH      = 2
ANCHOR_NORTH_WEST = 3
ANCHOR_NORTH_EAST = 4
ANCHOR_SOUTH      = 5
ANCHOR_SOUTH_WEST = 6
ANCHOR_SOUTH_EAST = 7
ANCHOR_WEST       = 8
ANCHOR_EAST       = 9

MOVE_TO  = 1
LINE_TO  = 2
CURVE_TO = 3
CLOSE    = 4

import ecell.event

class CanvasWidgetWrapper:
    def getBounds( self ):
        raise NotImplementedError

    def convertCoordToPixels( self, coord ):
        raise NotImplementedError

    def convertSizeToPixels( self, size ):
        raise NotImplementedError

    def convertCoordToLogical( self, coord ):
        raise NotImplementedError

    def convertSizeToLogical( self, size ):
        raise NotImplementedError

    def setCanvasSize( self, size ):
        raise NotImplementedError

    def getCanvasSize( self ):
        raise NotImplementedError

    def getItemAt( self, coord ):
        raise NotImplementedError

class CanvasEvent( ecell.event.Event ):
    def fromGdkEvent( self, source, e ):
        if e.type == gtk.gdk.BUTTON_PRESS:
            retval = MouseEvent(
                'pressed', source,
                button = e.button,
                pos = ( e.x, e.y ),
                root = ( e.x_root, e.y_root ) )
        elif e.type == gtk.gdk.BUTTON_RELEASE:
            retval = MouseEvent( 'released', source,
                button = e.button,
                pos = ( e.x, e.y ),
                root = ( e.x_root, e.y_root ) )
        elif e.type == gtk.gdk.MOTION_NOTIFY:
            retval = MouseEvent( 'moved', source,
                pos = ( e.x, e.y ) )
        elif e.type == gtk.gdk.ENTER_NOTIFY:
            retval = MouseEvent( 'entered', source,
                pos = ( e.x, e.y ) )
        elif e.type == gtk.gdk.LEAVE_NOTIFY:
            retval = MouseEvent( 'left', source,
                pos = ( e.x, e.y ) )
        elif e.type == gtk.gdk._2BUTTON_PRESS:
            retval = MouseEvent(
                'double_clicked', source,
                button = e.button,
                pos = ( e.x, e.y ),
                root = ( e.x_root, e.y_root ) )
        elif e.type == gtk.gdk._3BUTTON_PRESS:
            retval = MouseEvent(
                'triple_clicked', source,
                button = e.button,
                pos = ( e.x, e.y ),
                root = ( e.x_root, e.y_root ) )
        else:
            raise RuntimeError, "Fix me!"
        return retval
    fromGdkEvent = classmethod( fromGdkEvent )

class KeyEvent( CanvasEvent ):
    pass

class MouseEvent( CanvasEvent ):
    pass

class CanvasItem:
    __slots__ = (
        'parent',
        )

    def addObserver( self, type, observer ):
        raise NotImplementedError

    def upper( self, another ):
        raise NotImplementedError

    def lower( self, another ):
        raise NotImplementedError

    def update( self ):
        raise NotImplementedError

    def convertCoordToWorld( self, coord ):
        raise NotImplementedError

    def convertSizeToWorld( self, size ):
        raise NotImplementedError

    def convertCoordToItem( self, coord ):
        raise NotImplementedError

    def convertSizeToItem( self, size ):
        raise NotImplementedError

    def grabCursor( self, cause, cursor = None ):
        raise NotImplementedError

    def ungrabCursor( self, cause ):
        raise NotImplementedError

    def dispose( self ):
        raise NotImplementedError

class BezierPath( CanvasItem ):
    __slots__ = (
        'strokeColor',
        'fillColor',
        'strokeWidth',
        'path'
        )

class Polygon( CanvasItem ):
    __slots__ = (
        'strokeColor',
        'fillColor',
        'strokeWidth',
        'points'
        )

class Polyline( CanvasItem ):
    __slots__ = (
        'color',
        'width',
        'points'
        )

class Rectangle( CanvasItem ):
    __slots__ = (
        'x',
        'y',
        'width',
        'height',
        'strokeColor',
        'fillColor',
        'strokeWidth'
        )

class Ellipse( CanvasItem ):
    __slots__ = (
        'x',
        'y',
        'width',
        'height',
        'strokeColor',
        'fillColor',
        'strokeWidth'
        )

class Image( CanvasItem ):
    __slots__ = (
        'x',
        'y',
        'anchor',
        'pixbuf'
        )

class Text( CanvasItem ):
    __slots__ = (
        'x',
        'y',
        'anchor',
        'font',
        'text'
        )

class Canvas( CanvasItem ):
    __slots__ = (
        'x',
        'y'
        )

    def drawBezierPath( self, outlineColor, fillColor, outlineWidth, outlineWidthScaled, path ):
        raise NotImplementedError

    def drawPolyline( self, color, width, widthScaled, points ):
        raise NotImplementedError

    def drawPolygon( self, outlineColor, fillColor, outlineWidth, outlineWidthScaled, points ):
        raise NotImplementedError

    def drawRectangle( self, x1, y1, x2, y2, outlineColor, fillColor, outlineWidth, outlineWidthScaled ):
        raise NotImplementedError

    def drawEllipse( self, x1, y1, x2, y2, outlineColor, fillColor, outlineWidth, outlineWidthScaled ):
        raise NotImplementedError

    def drawText( self, x, y, color, anchor, size, text ):
        raise NotImplementedError

    def drawImage( self, x, y, anchor, pixbuf ):
        raise NotImplementedError

    def createChild( self, x, y ):
        raise NotImplementedError
