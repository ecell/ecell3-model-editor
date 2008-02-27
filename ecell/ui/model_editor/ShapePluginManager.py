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
import imp
import os

import config
from ShapeDescriptor import *
from Constants import *


class ShapePluginManager:
    def __init__(self):
        self.theShapeDescriptors = {}
        theTmpList=[]
        theFileNameList=[]
        for plugin_path_elem in config.plugin_path:
            theTmpList=os.listdir( plugin_path_elem )
            
            for line in theTmpList:
                if line.endswith(".py"):
                    newline=line.replace(".py","")
                    theFileNameList+=[newline]

            for value in theFileNameList:
                aFp, aPath, self.theDescription = imp.find_module(
                    value, [ plugin_path_elem, '.'] )
                module = imp.load_module(
                    value, aFp, aPath, self.theDescription )
                aShapeType = module.SHAPE_PLUGIN_TYPE
                if aShapeType not in self.theShapeDescriptors.keys():
                    self.theShapeDescriptors[aShapeType] = {}
                self.theShapeDescriptors[aShapeType][ module.SHAPE_PLUGIN_NAME ] = module

    def getShapeList(self,aShapeType):
        return self.theShapeDescriptors[ aShapeType ].keys()

    def createShapePlugin(self,aShapeType,aShapeName,EditorObject,graphUtils, aLabel):
        aShapeModule=self.theShapeDescriptors[aShapeType][aShapeName]
        aShapeSD=apply(aShapeModule.__dict__[os.path.basename(aShapeModule.__name__)],[EditorObject,graphUtils,aLabel])  
        return aShapeSD
        
    def getMinDims( self, aShapeType, aShapeName, graphUtils, aLabel ):
        aShapeModule=self.theShapeDescriptors[aShapeType][aShapeName]
        return apply( aShapeModule.__dict__["estLabelDims"],[graphUtils, aLabel] )
            
        

           
        
    
