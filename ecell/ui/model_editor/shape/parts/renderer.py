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

import ecell.ui.model_editor.canvas as cv
from ecell.ui.model_editor.shape.parts import *
from ecell.ui.model_editor.shape.parts.molds import *

__all__ = (
    'Renderer',
    )

class Renderer( object ):
    __slots__ = (
        'parent',
        'manager',
        'shape',
        'canvas',
        'molds',
        'moldToPartMap',
        'idToPartMap',
        'functionToPartsMap'
        )

    def __init__( self, parent, manager, shape, canvas ):
        self.parent = parent
        self.manager = manager
        self.shape = shape
        self.canvas = canvas
        self.molds = []
        self.moldToPartMap = {}
        self.idToPartMap = {}
        self.functionToPartsMap = {}

    def render( self, mold ):
        if isinstance( mold, BezierPathPartMold ):
            part = self.__renderBezierPathPart( mold )
        elif isinstance( mold, RectanglePartMold ):
            part = self.__renderRectanglePart( mold )
        elif isinstance( mold, EllipsePartMold ):
            part = self.__renderEllipsePart( mold )
        elif isinstance( mold, PolylinePartMold ):
            part = self.__renderPolylinePart( mold )
        elif isinstance( mold, PolygonPartMold ):
            part = self.__renderPolygonPart( mold )
        elif isinstance( mold, TextPartMold ):
            part = self.__renderTextPart( mold )
        elif isinstance( mold, ImagePartMold ):
            part = self.__renderImagePart( mold )
        elif isinstance( mold, PartMolds ):
            part = self.__renderParts( mold )
        if mold.function:
            part.canvasItem.addObserver( cv.CanvasEvent,
                lambda ev: self.shape.handleCanvasEvent( part, ev ) )
        self.molds.append( part )
        self.moldToPartMap[ mold ] = part
        if mold.id != None:
            self.idToPartMap[ mold.id ] = part
            if self.parent != None:
                self.parent[ mold.id ] = part
        if mold.function != None:
            self.functionToPartsMap.setdefault( mold.function, [] ).append( part )
        return part

    def __renderParts( self, mold ):
        part = Parts( mold, self.shape, self.parent )
        pos = self.shape.evalParameter( part, mold.pos )
        part.canvasItem = self.canvas.createChild(
            x = pos[ 0 ],
            y = pos[ 1 ]
            )
        if mold.size != None:
            bounds = part.canvasItem.bounds
            size = ( bounds[ 2 ] - bounds[ 0 ], bounds[ 3 ] - bounds[ 1 ] )
            _size = self.shape.evalParameter( part, mold.size )
            if mold.size[ 0 ] != 0 and mold.size[ 1 ] != 0 and \
               size[ 0 ] != 0 and size[ 1 ] != 0:
                part.canvasItem.transform = (
                    0, 0, 
                    _size[ 0 ] / size[ 0 ], 0,
                    0, _size[ 1 ] / size[ 1 ]
                    )
        rdr = Renderer( part, self.manager, self.shape, part.canvasItem )
        for child in mold.children:
            rdr.render( child )

        for child in rdr.molds:
            if child.mold.above != None:
                child.canvasItem.upper(
                    rdr.idToPartMap[ child.mold.above ].canvasItem )
            elif child.mold.below != None:
                child.canvasItem.lower(
                    rdr.idToPartMap[ child.mold.below ].canvasItem )

        self.idToPartMap.update( rdr.idToPartMap )
        self.moldToPartMap.update( rdr.moldToPartMap )
        for k, v in rdr.functionToPartsMap.iteritems():
            parts = self.functionToPartsMap.setdefault( k, [] )
            parts += v
        self.molds += rdr.molds
        return part

    def __renderBezierPathPart( self, mold ):
        part = BezierPathPart( mold, self.shape, self.parent )
        part.canvasItem = self.canvas.drawBezierPath(
            strokeColor = self.shape.evalParameter( part, mold.strokeColor ),
            fillColor   = self.shape.evalParameter( part, mold.fillColor ),
            path        = self.shape.evalParameter( part, mold.path ),
            strokeWidth = self.shape.evalParameter( part, mold.strokeWidth )
            )
        return part

    def __renderRectanglePart( self, mold ):
        part = RectanglePart( mold, self.shape, self.parent )
        rect = self.shape.evalParameter( part, mold.rect )
        part.canvasItem = self.canvas.drawRectangle(
            x           = rect[ 0 ],
            y           = rect[ 1 ],
            width       = rect[ 2 ],
            height      = rect[ 3 ],
            strokeColor = self.shape.evalParameter( part, mold.strokeColor ),
            fillColor   = self.shape.evalParameter( part, mold.fillColor ),
            strokeWidth = self.shape.evalParameter( part, mold.strokeWidth )
            )
        return part

    def __renderEllipsePart( self, mold ):
        part = EllipsePart( mold, self.shape, self.parent )
        rect = self.shape.evalParameter( part, mold.rect )
        part.canvasItem = self.canvas.drawEllipse(
            x           = rect[ 0 ],
            y           = rect[ 1 ],
            width       = rect[ 2 ],
            height      = rect[ 3 ],
            strokeColor = self.shape.evalParameter( part, mold.strokeColor ),
            fillColor   = self.shape.evalParameter( part, mold.fillColor ),
            strokeWidth = self.shape.evalParameter( part, mold.strokeWidth )
            )
        return part

    def __renderPolylinePart( self, mold ):
        part = PolylinePart( mold, self.shape, self.parent )
        part.canvasItem = self.canvas.drawPolyline(
            color  = self.shape.evalParameter( part, mold.color ),
            width  = self.shape.evalParameter( part, mold.width ),
            points = self.shape.evalParameter( part, mold.points )
            )
        return part

    def __renderPolygonPart( self, mold ):
        part = PolygonPart( mold, self.shape, self.parent )
        part.canvasItem = self.canvas.drawPolygon(
            strokeColor = self.shape.evalParameter( part, mold.strokeColor ),
            fillColor   = self.shape.evalParameter( part, mold.fillColor ),
            strokeWidth = self.shape.evalParameter( part, mold.strokeWidth ),
            points      = self.shape.evalParameter( part, mold.points )
            )
        return part

    def __renderTextPart( self, mold ):
        part = TextPart( mold, self.shape, self.parent )
        pos = self.shape.evalParameter( part, mold.pos )
        part.canvasItem = self.canvas.drawText(
            color   = self.shape.evalParameter( part, mold.color ),
            x       = pos[ 0 ],
            y       = pos[ 1 ],
            anchor  = self.shape.evalParameter( part, mold.anchor ),
            font    = self.shape.evalParameter( part, mold.font ),
            text    = self.shape.evalParameter( part, mold.text )
            )
        return part

    def __renderImage( self, mold ):
        part = ImagePart( mold, self.shape, self.parent )
        pos = self.shape.evalParameter( part, mold.pos )
        part.canvasItem = self.canvas.drawImage(
            x      = pos[ 0 ],
            y      = pos[ 1 ],
            anchor = self.shape.evalParameter( part, mold.anchor ),
            pixbuf = self.shape.evalParameter( part, mold.pixbuf )
            )
        return part


