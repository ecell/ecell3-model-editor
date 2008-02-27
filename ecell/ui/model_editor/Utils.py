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
from Constants import *
from ConfirmWindow import *
import re

def getUniqueVarrefName ( aVarrefList, aVarrefName = None ):
    # get existing varrefnamelist
    nameList = []
    for aVarref in aVarrefList:
        nameList.append( aVarref[values.VARREF_NAME] )

    # get initial varrefname
    if aVarrefName == None:
        aVarrefName = '___'
    elif aVarrefName not in nameList:
        return aVarrefName
    counter = 0 
    # try other values
    incVarrefName = aVarrefName + str( counter )
    while incVarrefName in nameList:
        incVarrefName = aVarrefName + str( counter )
    return incVarrefName
    
def showPopupMessage( aMode, aMessage, aTitle = 'Confirm' ):
    msgWin = ConfirmWindow( aMode, aMessage, aTitle )
    return msgWin.return_result()

def showPicker( choice, aMessage, aTitle = 'Pick one' ):
    msgWin = ConfirmWindow( CUSTOM_MODE, aMessage, choice, aTitle )
    return msgWin.return_result()
    
