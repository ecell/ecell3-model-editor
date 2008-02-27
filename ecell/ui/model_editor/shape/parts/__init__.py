#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#
#       This file is mold of the E-Cell System
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

__all__ = (
    'Part',
    'Parts',
    'BezierPathPart',
    'RectanglePart',
    'EllipsePart',
    'PolylinePart',
    'PolygonPart',
    'TextPart',
    'ImagePart',
    )

class Part( object ):
    __slots__ = (
        'shape',
        'canvasItem',
        'mold',
        'parent',
        'items'
        )

    def __init__( self, mold = None, shape = None, parent = None, canvasItem = None ):
        self.mold = mold
        self.shape = shape
        self.parent = parent
        self.canvasItem = canvasItem
        self.items = {}

    def __setitem__( self, key, val ):
        self.items[ key ] = val

    def __getitem__( self, key ):
        if self.items.has_key( key ):
            return self.items[ key ]
        elif self.mold.has_key( key ):
            return self.mold[ key ]
        else:
            return getattr( self.canvasItem, key )

    def has_key( self, key ):
        return self.items.has_key( key ) or \
            self.mold.has_key( key ) or \
            hasattr( self.canvasItem, key )

class Parts( Part ):
    def __getPos( self ):
        return ( self.canvasImage.x, self.canvasImage.y )
    pos = property( __getPos )

    def update( self ):
        if self.mold.pos != None:
            pos = self.shape.evalParameter( self, self.mold.pos )
            self.canvasItem.x = pos[ 0 ]
            self.canvasItem.y = pos[ 1 ]
        if self.mold.size != None:
            _size = self.shape.evalParameter( self, self.mold.size )
            bounds = self.canvasItem.bounds
            size = ( bounds[ 2 ] - bounds[ 0 ], bounds[ 3 ] - bounds[ 1 ] )
            if _size[ 0 ] != 0 and _self.mold.size[ 1 ] != 0 and \
               size[ 0 ] != 0 and size[ 1 ] != 0:
                self.canvasItem.transform = (
                    0, 0, 
                    _size[ 0 ] / size[ 0 ], 0,
                    0, _size[ 1 ] / size[ 1 ]
                    )
        self.canvasItem.update()

class BezierPathPart( Part ):
    def __getStrokeColor( self ):
        return self.canvasItem.strokeColor
    strokeColor = property( __getStrokeColor )

    def __getFillColor( self ):
        return self.canvasItem.fillColor
    fillColor = property( __getFillColor )

    def __getPath( self ):
        return self.canvasItem.path
    path = property( __getPath )

    def __getStrokeWidth( self ):
        return self.canvasItem.path
    strokeWidth = property( __getStrokeWidth )

    def update( self ):
        self.canvasItem.strokeColor = self.shape.evalParameter(
                self, self.mold.strokeColor )
        self.canvasItem.fillColor   = self.shape.evalParameter(
                self, self.mold.fillColor )
        self.canvasItem.path        = self.shape.evalParameter(
                self, self.mold.path )
        self.canvasItem.strokeWidth = self.shape.evalParameter(
                self, self.mold.strokeWidth )
        #self.canvasItem.update()

class RectanglePart( Part ):
    def __getRect( self ):
        return (
            self.canvasItem.x,
            self.canvasItem.y,
            self.canvasItem.width, 
            self.canvasItem.height
            )
    rect = property( __getRect )

    def __getSize( self ):
        return ( self.canvasItem.width, self.canvasItem.height )
    size = property( __getSize )
    def __getWidth( self ):
        return self.canvasItem.width
    width = property( __getWidth )

    def __getHeight( self ):
        return self.canvasItem.height
    height = property( __getHeight )

    def __getStrokeColor( self ):
        return self.canvasItem.strokeColor
    strokeColor = property( __getStrokeColor )

    def __getFillColor( self ):
        return self.canvasItem.fillColor
    fillColor = property( __getFillColor )

    def __getStrokeWidth( self ):
        return self.canvasItem.strokeWidth
    strokeWidth = property( __getStrokeWidth )

    def update( self ):
        rect = self.shape.evalParameter( self, self.mold.rect )
        self.canvasItem.x           = rect[ 0 ]
        self.canvasItem.y           = rect[ 1 ]
        self.canvasItem.width       = rect[ 2 ]
        self.canvasItem.height      = rect[ 3 ]
        self.canvasItem.strokeColor = self.shape.evalParameter(
                self, self.mold.strokeColor )
        self.canvasItem.fillColor   = self.shape.evalParameter(
                self, self.mold.fillColor )
        self.canvasItem.strokeWidth = self.evalParameter(
                self, self.mold.strokeWidth )
        #self.canvasItem.update()

class EllipsePart( Part ):
    def __getRect( self ):
        return (
            self.canvasItem.x,
            self.canvasItem.y,
            self.canvasItem.width, 
            self.canvasItem.height
            )
    rect = property( __getRect )

    def __getStrokeColor( self ):
        return self.canvasItem.strokeColor
    strokeColor = property( __getStrokeColor )

    def __getFillColor( self ):
        return self.canvasItem.fillColor
    fillColor = property( __getFillColor )

    def __getStrokeWidth( self ):
        return self.canvasItem.strokeWidth
    strokeWidth = property( __getStrokeWidth )

    def update( self ):
        rect = self.shape.evalParameter( self, self.mold.rect )
        self.canvasItem.x           = rect[ 0 ]
        self.canvasItem.y           = rect[ 1 ]
        self.canvasItem.width       = rect[ 2 ]
        self.canvasItem.height      = rect[ 3 ]
        self.canvasItem.strokeColor = self.shape.evalParameter(
                self, self.mold.strokeColor )
        self.canvasItem.fillColor   = self.shape.evalParameter(
                self, self.mold.fillColor )
        self.canvasItem.strokeWidth = self.shape.evalParameter(
                self, self.mold.strokeWidth )
        #self.canvasItem.update()

class PolylinePart( Part ):
    def __getColor( self ):
        return self.canvasItem.color
    color = property( __getColor )

    def __getWidth( self ):
        return self.canvasItem.width
    width = property( __getWidth )

    def __getPoints( self ):
        return self.canvasItem.points
    points = property( __getPoints )

    def update( self ):
        self.canvasItem.color  = self.shape.evalParameter(
                self, self.mold.color )
        self.canvasItem.width  = self.shape.evalParameter(
                self, self.mold.width )
        self.canvasItem.points = self.shape.evalParameter(
                self, self.mold.points )
        #self.canvasItem.update()

class PolygonPart( Part ):
    def __getStrokeColor( self ):
        return self.canvasItem.strokeColor
    strokeColor = property( __getStrokeColor )

    def __getFillColor( self ):
        return self.canvasItem.fillColor
    fillColor = property( __getFillColor )

    def __getStrokeWidth( self ):
        return self.canvasItem.strokeWidth
    strokeWidth = property( __getStrokeWidth )

    def __getPoints( self ):
        return self.canvasItem.points
    points = property( __getPoints )
    def update( self ):
        self.canvasItem.strokeColor = self.shape.evalParameter(
                self, self.mold.strokeColor ),
        self.canvasItem.fillColor   = self.shape.evalParameter(
                self, self.mold.fillColor ),
        self.canvasItem.strokeWidth = self.shape.evalParameter(
                self, self.mold.strokeWidth ),
        self.canvasItem.points      = self.shape.evalParameter(
                self, self.mold.points )
        #self.canvasItem.update()

class TextPart( Part ):
    def __getPos( self ):
        return ( self.canvasImage.x, self.canvasImage.y )
    pos = property( __getPos )

    def __getColor( self ):
        return self.canvasItem.color
    color = property( __getColor )

    def __getAnchor( self ):
        return self.canvasItem.anchor
    anchor = property( __getAnchor )

    def __getFont( self ):
        return self.canvasItem.font
    font = property( __getFont )

    def __getText( self ):
        return self.canvasItem.text
    text = property( __getText )

    def __getSize( self ):
        return ( self.canvasItem.width, self.canvasItem.height )
    size = property( __getSize )

    def __getWidth( self ):
        return self.canvasItem.width
    width = property( __getWidth )

    def __getHeight( self ):
        return self.canvasItem.height
    height = property( __getHeight )

    def __getRect( self ):
        return (
            self.canvasItem.x, self.canvasItem.y,
            self.canvasItem.width, self.canvasItem.height
            )
    rect = property( __getRect )

    def update( self ):
        pos = self.shape.evalParameter( self, self.mold.pos )
        self.canvasItem.x       = pos[ 0 ]
        self.canvasItem.y       = pos[ 1 ]
        self.canvasItem.color   = self.shape.evalParameter(
                self, self.mold.color )
        self.canvasItem.anchor  = self.shape.evalParameter( self, self.mold.anchor )
        self.canvasItem.font    = self.shape.evalParameter(
                self, self.mold.font )
        self.canvasItem.text    = self.shape.evalParameter(
                self, self.mold.text )
        #self.canvasItem.update()

class ImagePart( Part ):
    def __getPos( self ):
        return ( self.canvasImage.x, self.canvasImage.y )
    pos = property( __getPos )

    def __getAnchor( self ):
        return self.canvasItem.anchor
    anchor = property( __getAnchor )

    def __getSize( self ):
        return ( self.canvasItem.width, self.canvasItem.height )
    size = property( __getSize )

    def __getWidth( self ):
        return self.canvasItem.width
    width = property( __getWidth )

    def __getHeight( self ):
        return self.canvasItem.height
    height = property( __getHeight )

    def __getRect( self ):
        return (
            self.canvasItem.x, self.canvasItem.y,
            self.canvasItem.width, self.canvasItem.height
            )
    rect = property( __getRect )

    def __getPixBuf( self ):
        return self.canvasItem.pixBuf
    pixbuf = property( __getPixBuf )

    def update( self ):
        pos = self.shape.evalParameter( self, self.mold.pos )
        self.canvasItem = canvas.drawImage
        self.canvasItem.x      = pos[ 0 ]
        self.canvasItem.y      = pos[ 1 ]
        self.canvasItem.anchor = self.shape.evalParameter(
                self, self.mold.anchor )
        self.canvasItem.pixbuf = self.shape.evalParameter( self, mold.pixbuf )
        #self.canvasItem.update()
