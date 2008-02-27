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

import os
import sys
import time
import string
import tempfile
import traceback
from ConfigParser import ConfigParser, NoOptionError

import gtk

import ecell.identifiers as identifiers
import ecell.eml
import ecell.util
from ecell.DMInfo import DMInfo
import ecell.model.objects as objs
from ecell.model.store import *
from ecell.ecs_constants import *

import ecell.ui.model_editor.config as config
from ecell.ui.model_editor.Constants import *
from ecell.ui.model_editor.Clipboard import Clipboard
from ecell.ui.model_editor.ShapePluginManager import ShapePluginManager
from ecell.ui.model_editor.Command import Command
from ecell.ui.model_editor.CommandQueue import CommandQueue
from ecell.ui.model_editor.PopupMenu import PopupMenu
from ecell.ui.model_editor.PathwayEditor import PathwayEditor
from ecell.ui.model_editor.LayoutManager import LayoutManager
from ecell.ui.model_editor.AutosaveWindow import AutosaveWindow
from ecell.ui.model_editor.MEMainWindow import MEMainWindow
from ecell.ui.model_editor.StepperTab import StepperTab
from ecell.ui.model_editor.EntityListTab import EntityListTab
from ecell.ui.model_editor.ClassEditorWindow import ClassEditorWindow
from ecell.ui.model_editor.AboutModelEditor import AboutModelEditor
from ecell.ui.model_editor.ObjectEditorWindow import ObjectEditorWindow
from ecell.ui.model_editor.ConnectionObjectEditorWindow import ConnectionObjectEditorWindow
from ecell.ui.model_editor.CommandMultiplexer import CommandMultiplexer
from ecell.ui.model_editor.LayoutEml import LayoutEml
from ecell.ui.model_editor.GraphicalUtils import GraphicalUtils

import ecell.ui.model_editor.Utils as utils

from ecell.ui.model_editor.LayoutBufferFactory import LayoutBufferFactory
from ecell.ui.model_editor.Runtime import Runtime, ResultsWindow

from ecell.ui.model_editor.LayoutCommand import *

from ecell.ui.model_editor.Error import *

__all__ = (
    'ModelEditor'
    )

PREDEFINED_GTK_STYLE = '''
style "smallchar" {
    font_name="Sans 8"
}

style "canvastext" {
    font_name="Sans Italic 10"
}

widget "MEMainWindow.top_frame.vbox10.vpaned1.handlebox24.*" style "smallchar"

class "GnomeCanvasText" style "canvastext"
'''

class ModelEditor:
    """
    class for holding together Model, Command, Buffer classes
    loads and saves model
    handles undo queue
    display messages
    """

    def findUserPrefsDir( self ):
        if not self.theUserPreferencesDir:
            path_list = (
                config.user_prefs_dir,
                config.home_dir
                )
            for parent_dir in path_list:
                path = os.path.join( parent_dir, CONFIG_FILE_NAME )
                if os.path.isfile( path ):
                    self.theUserPreferencesDir = parent_dir
            self.theUserPreferencesDir = path_list[0]
        return self.theUserPreferencesDir

    def findIniFile( self ):
        path_list = ( self.findUserPrefsDir(), ) + (
            config.conf_dir,
            config.lib_dir
            )
        for parent_dir in path_list:
            path = os.path.join( parent_dir, CONFIG_FILE_NAME )
            if os.path.isfile( path ):
                return path
        return None

    def initUI( self ):
        gtk.rc_parse_string(PREDEFINED_GTK_STYLE)
        self.theStepperWindowList = []
        self.theEntityListWindowList = []
        self.thePathwayEditorList = []
        self.theClassEditor = None
        self.theResultsWindow = None
        self.theObjectEditorWindow = None
        self.theConnObjectEditorWindow = None
        self.theAboutModelEditorWindow = None
        self.theFullIDBrowser = None
        self.thePopupMenu = PopupMenu( self )
        self.theMainWindow = MEMainWindow( self )
        self.openAutosaveWindow = False
        self.theAutosaveWindow = None
        self.theGraphicalUtils = GraphicalUtils( self.theMainWindow )
        self.createNewModel()

    def __init__( self, aFileName = None ):
        self.theUserPreferencesDir = None
        self.theRuntimeObject = Runtime(self)

        aIniFileName = self.findIniFile()
        aConfigDB = ConfigParser()
        if aIniFileName != None:
            aConfigDB.read( aIniFileName )
        self.theConfigDB = aConfigDB
        self.theIniFileName = aIniFileName

        self.theClipboard = Clipboard()        
        self.copyBuffer = None

        # set up load and save dir
        self.loadDirName = os.getcwd()
        self.saveDirName = os.getcwd()
        print "Reading dynamic modules, please wait..."
        self.theDMInfo = DMInfo()

        # create variables
        self.loadRecentFileList()

        self.theUpdateInterval = 0
        self.operationCount = 0
        self.theTimer = None

        self.theModel = None
        self.theModelName = ''
        self.theModelFileName = ''

        self.operationCount=1
        
        self.thePropertyName = []        
        self.changesSaved = True
        self.modelHasName = False
        self.openAboutModelEditor = False
        self.isNameConfirmed = False
        self.executionTime = 0
        self.executionSteps = 0

        self.theLayoutManager = LayoutManager( self )
        self.theMultiplexer = CommandMultiplexer( self, self.theLayoutManager )
        self.theUndoQueue = CommandQueue(MAX_REDOABLE_COMMAND)
        self.theRedoQueue = CommandQueue(MAX_REDOABLE_COMMAND)
        self.theEntityType = DM_TYPE_VARIABLE

    def getShapePluginManager(self):
        self.theShapePluginManager=ShapePluginManager()
        if(self.theShapePluginManager !=None):
            return self.theShapePluginManager
       
    def quitApplication( self ):
        if not self.closeModel():
            return False
        gtk.main_quit()
        return True
   
    def createNewModel( self ):
        """ 
        in:
        returns True if successful, false if not
        """
        # create new Model
        if not self.createModel():
            return False

        self.theModel.createStepper(
            DE_DEFAULT_STEPPER_CLASS,
            DE_DEFAULT_STEPPER_NAME)
        self.theModel.setEntityProperty(
            identifiers.FullPN( 'System::/:StepperID' ),
            DE_DEFAULT_STEPPER_NAME)
        newFullID = identifiers.FullID( VARIABLE, '/', 'SIZE' )
        self.theModel.createEntity( 'Variable', newFullID )
        self.theModel.setEntityProperty(
            newFullID.createFullPN( 'Value' ), 1 )
        self.changesSaved = True
        self.updateWindows()
        self.createPathwayWindow()
        return True

    def validateModel( self ):
        utils.showPopupMessage(
            utils.OK_MODE,
            "Sorry, not implemented!",
            ME_ERROR )

    def convertSbmlToEml(self, sbmlFileName):
        tmpFileBaseName = os.path.basename(sbmlFileName)   
        tmpFileName, tmpEx = os.path.splitext( tmpFileBaseName )
        
        #Output filename 
        tmpFileName = str(self.getTmpDir()) + os.sep + tmpFileName + '.eml' 
        os.system( 'ecell3-sbml2eml -o "'+ tmpFileName + '" "' + sbmlFileName +'"' )
        return tmpFileName

    def convertEmlToSbml(self, emlFileName, sbmlFileName):
        #emlName, tmpEx = os.path.splitext( emlFileName )
        #sbmlFileName = emlName + ".sbml"
        if os.path.exists( sbmlFileName ):
            if utils.showPopupMessage(
                    utils.OKCANCEL_MODE,
                    "%s already exists. Do you want to replace it?" % aFileName,
                    ME_OKCANCEL ) != utils.OK_PRESSED:
                return False
        # create window
        buttons = [ "Version 1\nLevel 1", "Version 1\nLevel 2", "Version 2" ]
        filecontent = [ "1\n1\n", "1\n2\n", "2\n" ]
        result = utils.showPicker( buttons,
            "Please choose SBML Version and Level!",
            "Choose SBML version" )
        if result == utils.CANCEL_PRESSED:
            return False

        #write file
        paramFileName = "__SBMLWriter__"
        fd = open( paramFileName,'w' )
        fd.write(filecontent[result] )
        fd.close()
        
        os.system(  'ecell3-eml2sbml -o "' + sbmlFileName + '" "' + emlFileName + '" <"' + paramFileName + '"')
        return True
    
    def convertEmToEml(self, emFileName):
        tmpFileBaseName = os.path.basename(emFileName)
        tmpFileName, tmpExt = os.path.splitext( tmpFileBaseName )
        tmpFileName = str(self.getTmpDir()) + os.sep + tmpFileName + '.eml'
        os.system( 'ecell3-em2eml -o "' + tmpFileName +'" "'+ emFileName + '"')
        return tmpFileName

    def convertEmlToEm(self, emlFileName, emFileName ):
        if os.path.exists( emFileName ):
            if utils.showPopupMessage(
                    utils.OKCANCEL_MODE,
                    "%s already exists. Do you want to replace it?" % aFileName,
                    ME_OKCANCEL ) != utils.OK_PRESSED:
                return False
        os.system( 'ecell3-eml2em -o "' + emFileName + '" "' + emlFileName + '"')
        return True

    def loadEmlAndLeml(self, aFileName):


        # tries to parse file
        try:
            aFileObject = open( aFileName, 'r' )
            anEml = ecell.Eml( aFileObject )
            # calls load methods
            self.loadStepper( anEml )
            self.loadEntity( anEml )
            self.loadProperty( anEml )
        except:
            #display message dialog
            utils.showPopupMessage(
                utils.OK_MODE,
                "Error loading file %s" % aFileName,
                ME_ERROR )
            anErrorMessage = "\n".join(
                    traceback.format_exception( sys.exc_type,sys.exc_value, \
                        sys.exc_traceback ) )
            self.printMessage( anErrorMessage )
            return False
        # load layouts
        try:
            self.loadLayoutEml( os.path.split( aFileName ) )
        except:
            #display message dialog
            utils.showPopupMessage(
                utils.OK_MODE,
                "Error loading layout information from file %s" % aFileName,
                ME_ERROR )
            anErrorMessage = "\n".join( traceback.format_exception(sys.exc_type,sys.exc_value, sys.exc_traceback)  )
            self.printMessage( anErrorMessage )
            return False
        return True

    def saveEmlAndLeml(self, aFileName):
        
        #aFileName = self.filenameFormatter(aFileName)
        # save layout eml
        if self.getMode() == ME_RUN_MODE:
            if not self.saveSimulator( aFileName ):
                return False
        elif not self.saveModelStore( aFileName ):
            return False
        return self.saveLayoutEml(os.path.split( aFileName ))

    def saveSimulator( self, aFileName ):
        try:
            self.theRuntimeObject.getSession().saveModel( aFileName )
        except:
            utils.showPopupMessage(
                utils.OK_MODE,
                "Error saving file %s" % aFileName,
                ME_ERROR )
            anErrorMessage = "\n".join( traceback.format_exception(sys.exc_type,sys.exc_value, sys.exc_traceback) )
            self.printMessage( anErrorMessage )
            self.theMainWindow.resetCursor()
            return False
        return True

    def saveModelStore( self, aFileName ):
        anEml = ecell.Eml()

        self.saveStepper( anEml )

        # creates root entity
        anEml.createEntity('System', 'System::/')
        # calls save methods
        self.saveEntity( anEml )
        self.saveProperty( anEml )
        # add comment
        aCurrentInfo = "<!-- created by ecell ModelEditor\ndate: %s\n-->\n<eml>" % time.asctime( time.localtime() )

        aString = anEml.asString()
        anEml.destroy()
        aBuffer = aString #+ aCurrentInfo

        try:
            aFileObject = open( aFileName, 'w' )
            aFileObject.write( aBuffer )
            aFileObject.close()
        except:
            #display message dialog
            utils.showPopupMessage(
                utils.OK_MODE,
                "Error saving file %s" % aFileName,
                ME_ERROR )
            anErrorMessage = "\n".join( traceback.format_exception(sys.exc_type,sys.exc_value, sys.exc_traceback) )
            self.printMessage( anErrorMessage )
            self.theMainWindow.resetCursor()
            return False
        return True

    def saveModelStoreAndLayout( self ):
        self.savedLayoutManager = self.theLayoutManager
        self.savedModelStore = self.theModel
        self.savedModelName = self.theModelName
        self.savedModelFileName = self.theModelFileName
        self.savedModelHasName = self.modelHasName
        self.savedChangesSaved = self.changesSaved
        self.cwd = os.getcwd()
        
    def restoreModelStoreAndLayout( self ):
        self.changesSaved = True
        self.createModel()
        self.theModel = self.savedModelStore
        self.theLayoutManager = self.savedLayoutManager
        self.createPathwayWindow()
        self.theModelName = self.savedModelName 
        self.theModelFileName = self.savedModelFileName
        self.modelHasName = self.savedModelHasName 
        self.changesSaved = self.savedChangesSaved 
        self.clearModelStoreAndLayoutSave()
        self.changeWorkingDir( self.cwd )
        self.updateWindows()
        return

    def clearModelStoreAndLayoutSave( self ):
        del self.savedLayoutManager
        del self.savedModelStore
        return

    def changeWorkingDir( self, aDirName ):
        if aDirName == "":
            return
        os.chdir( aDirName )
        self.theDMInfo.setWorkingDir( aDirName )
        self.theDMInfo.refresh()
        
    def loadModel ( self, aFileName ):
        """
        in: nothing
        returns True if some model is loaded or restored, False if nothing happened
        """

        # check if it is dir or/and file
        if os.path.isdir( aFileName ):
            self.loadDirName = aFileName.rstrip( os.sep )
            return False
        if not os.path.isfile( aFileName ):
            utils.showPopupMessage(
                utils.OK_MODE,
                "%s file cannot be found!" % aFileName,
                ME_ERROR )
            return False
        self.saveModelStoreAndLayout()

        # create new model
        if not self.createModel():
            return False


        self.theMainWindow.displayHourglass()

        aDirName = os.path.split( aFileName)[0]

        self.changeWorkingDir( aDirName )
    
        anExt = os.path.splitext(aFileName)[1].lower()
        
        if anExt == '.em':
            aTmpFileName = self.convertEmToEml(aFileName)
            # aTmpFileName has .eml extension
            if not self.loadEmlAndLeml(aTmpFileName):
                self.theMainWindow.resetCursor()
                self.restoreModelStoreAndLayout()
                return True
                
             # Remove the model residing in /tmp
            os.remove( aTmpFileName )
            self.isNameConfirmed = False

        elif anExt in ['.sbml', '.xml']:
            aTmpFileName = self.convertSbmlToEml(aFileName)
            if not self.loadEmlAndLeml(aTmpFileName):
                self.theMainWindow.resetCursor()
                self.restoreModelStoreAndLayout()
                return True
            os.remove( aTmpFileName )
            self.isNameConfirmed = False

        #try to load as .eml
        else: #anExt == '.eml':
            if not self.loadEmlAndLeml(aFileName):
                self.theMainWindow.resetCursor()
                self.restoreModelStoreAndLayout()
                return True
            self.isNameConfirmed = True

        self.loadDirName = os.path.split( aFileName )[0]            
        # log to recent list
        self.addToRecentFileList( aFileName )
        
        self.theModelFileName = aFileName

        self.theModelName = os.path.split( aFileName )[1]
        self.modelHasName = True
        self.changesSaved = True
        self.printMessage(
            "Model %s loaded successfully." % aFileName )
        self.updateWindows()
       
        self.createPathwayWindow( False )
        self.theMainWindow.resetCursor()
        self.loadDirName = os.getcwd()
        return True
        
    def createPathwayWindow( self, emptyFile = True ):
        aLayoutList = self.theLayoutManager.getLayoutNameList()
        if len( aLayoutList ) == 0:
            if emptyFile:
                layoutName = self.theLayoutManager.getUniqueLayoutName()
                aCommand = CreateLayout(
                    self.theLayoutManager, layoutName, True )
                self.doCommandList( [ aCommand ] )
            else:
                self.createEntityWindow()
        else:
            layoutName = aLayoutList[0]
            aLayout = self.theLayoutManager.getLayout( layoutName ) 
            self.createPathwayEditor( aLayout )

    def saveModel( self,  aFileName = None ):
        """
        in: bool saveAsFlag
        returns nothing
        """
        

        # check if it is dir
        if os.path.isdir( aFileName ):
            self.saveDirName = aFileName.rstrip(os.sep)
            return
        if self.getMode() == ME_RUN_MODE:
            if utils.showPopupMessage(
                    utils.YESNO_MODE,
                    "You are in Run mode now. \n" \
                    + "If you continue with save, all values will be saved " \
                    + "with their actual values in the Simulator right now " \
                    + "and not with the initial values set by you.\n" \
                    + "Do you want to proceed? ( Simulator will be stopped.)",
                    ME_YESNO ) != utils.OK_PRESSED:
                return
            if self.isRunning():
                self.theRuntimeObject.stop()
            
        self.theMainWindow.displayHourglass()

        self.saveDirName = os.path.split( aFileName )[0]

        aFileBaseName = os.path.basename(aFileName)
        anExt = os.path.splitext(aFileBaseName)[1].lower()

        if anExt == '.em':  
            aTmpFileName = self.getEmlTmpFileName( aFileName)

            self.saveEmlAndLeml( aTmpFileName )

            if self.convertEmlToEm( aTmpFileName, aFileName ) == False:
                os.remove( aTmpFileName )
                os.remove(os.path.splitext( aTmpFileName)[0] + '.leml')
                self.theMainWindow.resetCursor()
                return
        
            utils.showPopupMessage(
                utils.OK_MODE,
                "Layouting information are not saved into .em format",
                ME_WARNING )
            os.remove( aTmpFileName )
            os.remove(os.path.splitext( aTmpFileName)[0] + '.leml')
            self.isNameConfirmed = False

        elif anExt in  ['.sbml', '.xml']:
            aTmpFileName = self.getEmlTmpFileName( aFileName)

            self.saveEmlAndLeml( aTmpFileName )
            if self.convertEmlToSbml( aTmpFileName, aFileName ) == False:
                os.remove( aTmpFileName )
                os.remove(os.path.splitext( aTmpFileName)[0] + '.leml')
                self.theMainWindow.resetCursor()
                return
            os.remove( aTmpFileName )
            os.remove(os.path.splitext( aTmpFileName)[0] + '.leml')
            self.isNameConfirmed = False
        else:

            self.saveEmlAndLeml(aFileName) 
            
        self.isNameConfirmed = True
        # log to recent list
        self.addToRecentFileList ( aFileName )
        self.isConverted = True
        self.theModelFileName = aFileName
        self.printMessage( "Model %s saved successfully." % aFileName )
        self.theModelName = os.path.split( aFileName )[1]
        self.modelHasName = True
        self.changesSaved = True
        
        
        self.changeWorkingDir( self.saveDirName )
        self.updateWindows()
        
        self.theMainWindow.resetCursor()

    def filenameFormatter(self, aFileName):
        aName, anExt = os.path.splitext(aFileName) 
        anExt = anExt.lower()
        if anExt in ['.xml','.sbml', '.eml', '.em']:
            return aFileName

        elif anExt == '.leml':
            return aName + ".eml"
        else:
            return aFileName + '.eml'

    def lemlExist(self,fileName):
        if os.path.isfile(fileName):
            return True
        else:
            return False

    def loadLayoutEml( self, (emlPath, emlName) ):
        
        fileName = os.path.join( emlPath, self.getLemlFromEml( emlName ) )
        if not self.lemlExist(fileName):
            return
        fileObject = open(fileName, "r")
        aLayoutEml = LayoutEml(fileObject)

        aLayoutNameList =  aLayoutEml.getLayoutList()
        # create layouts

        for aLayoutName in  aLayoutNameList:
            self.theLayoutManager.createLayout(aLayoutName)
            aLayout = self.theLayoutManager.getLayout(aLayoutName)
        # create layoutproperties
        
            propList = aLayoutEml.getLayoutPropertyList(aLayoutName)
            for aProp in propList:
                aPropValue =aLayoutEml.getLayoutProperty(aLayoutName,aProp)
                if aPropValue == "False":
                    aPropValue=False
                elif aPropValue == "True":
                    aPropValue=True
                aLayout.setProperty(aProp,aPropValue)
                
            aRootID = aLayout.getProperty( LO_ROOT_SYSTEM )
            self.loadObject( aLayout, aRootID, aLayoutEml, None)
            aConnObjectList = aLayoutEml.getObjectList(OB_PROP_TYPE_CONNECTION, aLayoutName)
            # finally read and create connections for layout
            for aConnID in aConnObjectList:
                aProAttachedID = aLayoutEml.getObjectProperty(aLayoutName, aConnID,CO_PROCESS_ATTACHED)
                aVarAttachedID =aLayoutEml.getObjectProperty(aLayoutName, aConnID,CO_VARIABLE_ATTACHED)
                aProRing = aLayoutEml.getObjectProperty(aLayoutName, aConnID,CO_PROCESS_RING)
                aVarRing = aLayoutEml.getObjectProperty(aLayoutName, aConnID,CO_VARIABLE_RING)
                aVarrefName =  aLayoutEml.getObjectProperty(aLayoutName, aConnID,CO_NAME)
                aLayout.createConnectionObject(aConnID, aProAttachedID, aVarAttachedID,  aProRing, aVarRing,PROCESS_TO_VARIABLE, aVarrefName )
                anObject =aLayout.getObject(aConnID)
                propList = aLayoutEml.getObjectPropertyList(aLayoutName, aConnID )
                for aProp in propList:
                    if aProp in (CO_PROCESS_ATTACHED, CO_VARIABLE_ATTACHED,CO_PROCESS_RING,CO_VARIABLE_RING, CO_NAME):
                        continue
                    aPropValue = aLayoutEml.getObjectProperty(aLayoutName, aConnID,aProp)
                    if aPropValue == None:
                        continue
                    if aPropValue=="False":
                        aPropValue=False
                    elif aPropValue=="True":
                        aPropValue=True
                    anObject.setProperty(aProp,aPropValue)

    def loadObject( self, aLayout, anObjectID,  aLayoutEml, parentSys ):
        aLayoutName = aLayout.getName()
        propList = aLayoutEml.getObjectPropertyList(aLayoutName, anObjectID )

        objectType = aLayoutEml.getObjectProperty(aLayoutName, anObjectID ,OB_PROP_TYPE)
        aFullID = aLayoutEml.getObjectProperty(aLayoutName, anObjectID ,OB_PROP_FULLID)
        if objectType != OB_PROP_TYPE_CONNECTION:
            x=aLayoutEml.getObjectProperty(aLayoutName, anObjectID ,OB_PROP_POS_X)
            y=aLayoutEml.getObjectProperty(aLayoutName, anObjectID ,OB_PROP_POS_Y)

            aLayout.createObject(anObjectID, objectType, aFullID,x, y, parentSys )
            anObject =aLayout.getObject(anObjectID)
            for aProp in propList:
                if aProp in ( OB_PROP_TYPE,OB_PROP_FULLID,OB_PROP_POS_X,OB_PROP_POS_Y) :
                    continue
                aPropValue = aLayoutEml.getObjectProperty(aLayoutName, anObjectID,aProp)
                if aPropValue == None :
                    continue
                if aPropValue == "False":
                    aPropValue = False
                elif aPropValue == "True":
                    aPropValue = True
                anObject.setProperty(aProp,aPropValue)
        # create subobjects
        if objectType == OB_PROP_TYPE_SYSTEM:
            anObjectList = self.getObjectList(aLayoutEml,aLayoutName, anObjectID)
            for anID in anObjectList:
                self.loadObject( aLayout, anID, aLayoutEml,anObject )
        
    def getObjectList(self,aLayoutEml,aLayoutName,aParentID):
        anObjectList=[]
        aProObjectList = aLayoutEml.getObjectList(OB_PROP_TYPE_PROCESS, aLayoutName, aParentID)
        aVarObjectList = aLayoutEml.getObjectList(OB_PROP_TYPE_VARIABLE, aLayoutName, aParentID)
        aSysObjectList = aLayoutEml.getObjectList(OB_PROP_TYPE_SYSTEM, aLayoutName, aParentID)
        aTextObjectList = aLayoutEml.getObjectList(OB_PROP_TYPE_TEXT, aLayoutName, aParentID)
        anObjectList = aProObjectList + aVarObjectList + aSysObjectList+ aTextObjectList
        return anObjectList

    def saveLayoutEml( self, (emlPath, emlName) ):
        fileName = os.path.join( emlPath, self.getLemlFromEml( emlName ) )
        aLayoutEml = LayoutEml()
        # create layouts
        for aLayoutName in self.theLayoutManager.getLayoutNameList():
            self.saveLayout( aLayoutName, aLayoutEml )

        aString = aLayoutEml.asString()
        aLayoutEml.destroy()
#       aBuffer = string.join( string.split(aString, '<leml>\n'), aCurrentInfo)
        aBuffer = aString
        try:
            aFileObject = open( fileName, 'w' )
            aFileObject.write( aBuffer )
            aFileObject.close()
        except:
            #display message dialog
            utils.showPopupMessage(
                utils.OK_MODE,
                "Error saving file %s" % fileName,
                ME_ERROR )
            anErrorMessage = "\n".join( traceback.format_exception(sys.exc_type,sys.exc_value, sys.exc_traceback) )
            self.printMessage( anErrorMessage )
            return False
        return True

    def saveLayout( self, aLayoutName, aLayoutEml ):
        aLayoutEml.createLayout( aLayoutName )
        # save properties
        aLayoutObject = self.theLayoutManager.getLayout( aLayoutName )
        propList = aLayoutObject.getPropertyList()
        for aProperty in propList:
            aValue = aLayoutObject.getProperty( aProperty)
            aLayoutEml.setLayoutProperty( aLayoutName, aProperty, aValue )
        # save objects
        aRootID = aLayoutObject.getProperty( LO_ROOT_SYSTEM )
        self.saveObject( aLayoutObject, aRootID, aLayoutEml )
        # save connections
        conList = aLayoutObject.getObjectList( OB_PROP_TYPE_CONNECTION )
        for aConID in conList:
            self.saveObject( aLayoutObject, aConID, aLayoutEml )

    def saveObject( self, aLayoutObject, anObjectID,  aLayoutEml, parentID = 'layout' ):
        aLayoutName = aLayoutObject.getName()
        # create object
        anObject = aLayoutObject.getObject( anObjectID )
        aType = anObject.getProperty( OB_PROP_TYPE )
        aLayoutEml.createObject(  aType, aLayoutName, anObjectID, parentID )

        # save properties
        propList = anObject.getPropertyList()
        for aProperty in propList:
            if aProperty in ( PR_CONNECTIONLIST, VR_CONNECTIONLIST ):
                continue
            aValue = anObject.getProperty( aProperty)

            aLayoutEml.setObjectProperty( aLayoutName, anObjectID, aProperty, aValue )

        # save subobjects
        if aType == OB_PROP_TYPE_SYSTEM:
            for anID in anObject.getObjectList():
                self.saveObject( aLayoutObject, anID, aLayoutEml, anObjectID )
            
    def getLemlFromEml( self, emlName ):
        trunk = emlName.split('.')
        if trunk[ len(trunk)-1] == 'eml':
            trunk.pop()
        return '.'.join( trunk ) + '.leml'
    
    def setupDNDDest( self, aWidget ):
        """
        in: any widget will be set up DND destination for dropping propertyvalues
        """
        destTarget = [ ( DND_PROPERTYVALUELIST_TYPE, 0, 800 ) ]
        aWidget.drag_dest_set( gtk.DEST_DEFAULT_ALL, destTarget, gtk.gdk.ACTION_COPY )
        aWidget.connect("drag-data-received", self.data_received )
        
    def data_received( self, *args ):
        # selection data is expecyed in a format of
        # "modelfile1 resultfile1 fullpn1 value range_min range_max,modelfile2 resultfile2 fullpn2 value range_min range_max"
        if not self.theRuntimeObject.changeToDesignMode():
            utils.showPopupMessage(
                utils.OK_MODE,
                "Property values were not updated.",
                ME_ERROR )
            return
        selectionData = args[4]
        selectionList = map(lambda x: x.split(" "), selectionData.data.split(",") )
        for anEntry in selectionList:
            fullPN = anEntry[2]
            newValue = anEntry[3]
            
            if len(fullPN.split(":")) == 2:
                aCommand = ChangeStepperProperty( self, fullPN.split(":")[0], fullPN.split(":")[1], newValue )
            else:
                aCommand = ChangeEntityProperty( self, fullPN, newValue )

            if aCommand.isExecutable():
                self.doCommandList( [ aCommand ] )
                self.printMessage(
                    "Property %s updated to %s." % ( fullPN, newValue ) )
            else:
                utils.showPopupMessage(
                    utils.OK_MODE,
                    "Illegal value or property doesnot exist for %s. " \
                    + "Property was not updated!" % fullPN,
                    ME_ERROR )

    def getUniqueEntityName( self, aType, aSystemPath ):
        """
        in: string aType, string aSystemPath
        returns string entityname or none if atype or asystempath doesnot exists
        """
        aType = ENTITYTYPE_STRING_LIST[ aType ]
        # get entitylist in system
        anEntityNameList = map( lambda i: i.localID,
            self.theModel.getEntity(
                aSystemPath.toFullID() ).getChildren( entityType = aType ) )
        # call getUniqueName
        return self.getUniqueName( aType, anEntityNameList )

    def getUniqueStepperName(self ):
        """
        in: nothing
        return string stepper name 
        """
        # get stepper list
        aStepperIDList = self.theModel.getStepperList()

        # call getUniquename
        return self.getUniqueName( 'Stepper', aStepperIDList )

    def getUniqueEntityPropertyName( self, aFullID ):
        """
        in: string aFullID
        returns new unique propertyname
        """
        # get Propertylist
        aPropertyList = self.theModel.getEntityPropertyList( aFullID )

        # call getUniquename
        return self.getUniqueName( 'Property', aPropertyList )

    def getUniqueStepperPropertyName( self, anID ):
        """
        in: string anIDon_LayoutButton_toggled
        returns new unique propertyname
        """
        # get Propertylist
        aPropertyList = self.theModel.getStepperPropertyList( anID )

        # call getUniquename
        return self.getUniqueName( 'Property', aPropertyList )

    def getDMInfo( self ):
        return self.theDMInfo

    def getDefaultStepperClass( self ):
        return self.theDMInfo.getClassList( DM_TYPE_STEPPER )[0]

    def getDefaultProcessClass( self ):
        classList = self.theDMInfo.getClassInfoList( type = DM_TYPE_PROCESS )
        if DE_DEFAULT_PROCESS_CLASS in classList:
            return DE_DEFAULT_PROCESS_CLASS
        else:
            return classList[0]

    def getRecentFileList(self):
        """
        in: nothing
        returns list of recently saved/loaded files
        """
        return self.theRecentFileList

    def getModel( self ):
        if self.getMode() == ME_DESIGN_MODE:
            return self.theModel
        else:
            return self.theRuntimeObject.theSession.theSimulator

    def createPopupMenu( self, aComponent, anEvent ):
        self.setLastUsedComponent( aComponent )
        self.thePopupMenu.open(  anEvent )

    def doCommandList( self, aCommandList ):
        undoCommandList = []
        aCommandList = self.theMultiplexer.processCommandList( aCommandList )
        # check if we are in design mode
        if not self.theRuntimeObject.checkState( ME_DESIGN_MODE ):
            return
              
        for aCommand in aCommandList:
            # execute commands
            if aCommand.isExecutable():
                aCommand.execute()
                ( aType, anID ) = aCommand.getAffectedObject()
        
                self.updateWindows( aType, anID )
                ( aType, anID ) = aCommand.getSecondAffectedObject()
                if aType == None and anID == None:
                    pass
                else:
                    self.updateWindows( aType, anID )
                undoCommand = aCommand.getReverseCommandList()
        
                # put undocommands into undoqueue
                if undoCommand != None:
                    undoCommandList.extend( undoCommand )

                # reset commands put commands into redoqueue
                aCommand.reset()

        if undoCommandList != []:
            self.theUndoQueue.push ( undoCommandList )
            self.theRedoQueue.push ( aCommandList )
            self.changesSaved = False

        self.theMainWindow.update()

        self.checkAutoSaveOption()

    def getMode(self):
        return self.theRuntimeObject.theMode

    def autoSave(self, aFileName = 'AutoSaveUntitled'):
        
        processId = os.getpid()        
        #If user has loaded a file, theModelName shouldn't be empty
        if self.theModelName != '' or self.theModelName != None:
            modelBaseName = os.path.splitext(self.theModelName)[0]            
            autoSaveName = str(os.getcwd()) + os.sep + modelBaseName +  ".sav.eml"
            
        #Default save aFileName
        else:
            autoSaveName = str(os.getcwd()) + os.sep + aFileName +  ".sav.eml"
        self.autoSaveName = autoSaveName
        if not self.isRunning():
            saveResult = self.saveEmlAndLeml(autoSaveName)

        if self.theUpdateInterval != 0:
            self.theTimer = gtk.timeout_add(self.theUpdateInterval, self.autoSave)         
        return saveResult
         
    def checkAutoSaveOption(self): #def OperationAutoSave
        self.theUpdateInterval = self.getAutosavePreferences()[0] *1000
        byOperation = self.getAutosavePreferences()[1]

        if self.theUpdateInterval != 0 and self.theTimer == None:
            self.autoSave()

        if byOperation !=0 :        
            if self.operationCount == byOperation:
                self.operationCount=1
                self.autoSave()     
            elif self.operationCount < byOperation:
                self.operationCount = self.operationCount +1

    def canUndo( self ):
        if self.theUndoQueue == None:
            return False
        return self.theUndoQueue.isPrevious()

    def canRedo( self ):
        if self.theRedoQueue == None:
            return False
        return self.theRedoQueue.isNext()

    def undoCommandList( self ):
        aCommandList = self.theUndoQueue.moveback()
        self.theRedoQueue.moveback()
        cmdList = aCommandList[:]
        cmdList.reverse()
        #############added by lilan
        if not self.theRuntimeObject.checkState( ME_DESIGN_MODE ):
            return
        for aCommand in cmdList:
            # execute commands
            if aCommand.isExecutable():
                aCommand.execute()
                ( aType, anID ) = aCommand.getAffectedObject()
                self.updateWindows( aType, anID )
                ( aType, anID ) = aCommand.getSecondAffectedObject()
                if aType == None and anID == None:
                    pass
                else:
                    self.updateWindows( aType, anID )
    
                aCommand.reset()
        self.changesSaved = False

    def redoCommandList( self ):
        aCommandList = self.theRedoQueue.moveforward()
        self.theUndoQueue.moveforward()
        if not self.theRuntimeObject.checkState( ME_DESIGN_MODE ):
            return

        for aCommand in aCommandList:
            # execute commands
            if aCommand.isExecutable():
                aCommand.execute()

                ( aType, anID ) = aCommand.getAffectedObject()
                self.updateWindows( aType, anID )
                ( aType, anID ) = aCommand.getSecondAffectedObject()
                if aType == None and anID == None:
                    pass
                else:
                    self.updateWindows( aType, anID )

                aCommand.reset()
        self.changesSaved = False

    def createStepperWindow( self ):
        newWindow = StepperTab(self,'top_frame' ) 
        self.theMainWindow.attachTab( newWindow, "Stepper" )   
        self.theStepperWindowList.append( newWindow )

    def createEntityWindow( self ):
        newWindow = EntityListTab( self )
        #self.theValue = newWindow.getValue()                           
        self.theMainWindow.attachTab( newWindow,"EntityList" )        
        self.theEntityListWindowList.append( newWindow )

    def createResultsWindow( self ):
        newWindow = ResultsWindow( self.theRuntimeObject.getSession(), self  )
        self.theMainWindow.attachTab( newWindow, "Results" )   
        self.theResultsWindow = newWindow

    def createClassWindow( self ):
        if self.theClassEditor == None:
            newWindow = ClassEditorWindow( self )
            self.theMainWindow.attachTab(newWindow,"Class Editor") 
            self.theClassEditorList.append( newWindow )

    def createPathwayEditor( self, aLayout ):
        newWindow = PathwayEditor( self, aLayout )
        self.theMainWindow.attachTab( newWindow, "Pathway" ) 
        self.thePathwayEditorList.append( newWindow )

    def toggleOpenLayoutWindow(self,isOpen):
        self.openLayoutWindow=isOpen

    def createObjectEditorWindow(self, aLayoutName, anObjectID ):
        if not self.openObjectEditorWindow:
            self.theObjectEditorWindow=ObjectEditorWindow(self, aLayoutName, anObjectID)
            self.openObjectEditorWindow=True
        else:
            self.theObjectEditorWindow.setDisplayObjectEditorWindow( aLayoutName, anObjectID)


    def createConnObjectEditorWindow(self, aLayoutName, anObjectID ):
        if not self.openConnObjectEditorWindow:
            self.theConnObjectEditorWindow=ConnectionObjectEditorWindow(self, aLayoutName, anObjectID)
            self.openConnObjectEditorWindow=True
        else:
            self.theConnObjectEditorWindow.setDisplayConnObjectEditorWindow( aLayoutName, anObjectID)


    def createAboutModelEditor(self):
        if not self.openAboutModelEditor:
            AboutModelEditor(self)

    def toggleAboutModelEditor(self,isOpen,anAboutModelEditorWindow):
        self.theAboutModelEditorWindow = anAboutModelEditorWindow
        self.openAboutModelEditor=isOpen
       

    def copy(self ):
        self.theLastComponent.copy()


    def cut( self ):
        self.theLastComponent.cut()


    def paste(self ):
        self.theLastComponent.paste()


    def getCopyBuffer( self ):
        if self.theClipboard.isClipboardChanged():
            self.copyBuffer = self.theLayoutManager.theLayoutBufferFactory.\
                        createBufferFromEml( self.theClipboard.pasteFromClipboard() )
        return self.copyBuffer



    def setCopyBuffer( self, aBuffer ):
        self.copyBuffer = aBuffer
        self.theClipboard.copyToClipboard( aBuffer.asEml() )



    def setLastUsedComponent( self, aComponent ):
        self.theLastComponent = aComponent
        self.theMainWindow.update()

    def getLastUsedComponent( self  ):
        return self.theLastComponent 
    
    def getADCPFlags( self ):
        if self.theLastComponent == None:
            return [ False, False, False, False ]
            #return [ False, False, False, False, False ]
        else:
            if self.copyBuffer == None:
                aType = None
            else:
                aType = self.copyBuffer.getType()
                
            return self.theLastComponent.getADCPFlags( aType )

    def setFullIDBrowser( self, aBrowser):
        self.theFullIDBrowser = aBrowser

    def updateWindows( self, aType = None, anID = None ):        
        # aType None means nothing to be updated
        for aStepperWindow in self.theStepperWindowList:
            # anID None means all for steppers
            aStepperWindow.update( aType, anID )

        for anEntityWindow in self.theEntityListWindowList:
            anEntityWindow.update( aType, anID )           
        if self.theObjectEditorWindow!=None:
            self.theObjectEditorWindow.update(aType, anID)
        if self.theConnObjectEditorWindow!=None:
            self.theConnObjectEditorWindow.update(aType, anID)

        for aPathwayEditor in self.thePathwayEditorList:
            aPathwayEditor.update( aType, anID )

        if self.theFullIDBrowser != None:
            self.theFullIDBrowser.update( aType,anID )
        if self.theMainWindow.exists():
            self.theMainWindow.update()
        
    def isRunning( self ):
        aSession = self.theRuntimeObject.getSession()
        if aSession != None:
            return aSession.isRunning()

    def closeModel( self ):
        """ 
        in: Nothing
        returns True if successful, False if not
        """
        if self.isRunning():
            self.theRuntimeObject.stop()

        if not self.changesSaved:
            if utils.showPopupMessage(
                    utils.YESNO_MODE,
                    "Changes are not saved.\n" \
                    + "Are you sure to close %s?" % self.theModelName,
                    ME_YESNO )  == utils.CANCEL_PRESSED:
                return False

        # close ModelStore
        self.theModel = None
        self.theLayoutManager = None

        # set name 
        self.theModelName = ''
        self.theModelFileName = ''
        self.theUndoQueue = None
        self.theRedoQueue = None
        self.changesSaved = True
        self.closeWindows()
        self.theRuntimeObject.closeModel()
        #self.updateWindows()
        return True

    def closeWindows( self ):
        for aStepperWindow in self.theStepperWindowList:
            # anID None means all for steppers
            aStepperWindow.close( )
        for anEntityWindow in self.theEntityListWindowList:
            anEntityWindow.close( )
        for aPathwayEditor in self.thePathwayEditorList:
            aPathwayEditor.close( )
        if self.theClassEditor != None:
            self.theClassEditor.deleted(None)
        if self.theResultsWindow != None:
            self.theResultsWindow.deleted( None )
            
        if self.theConnObjectEditorWindow!=None:
            self.theConnObjectEditorWindow.destroy()
        if self.theObjectEditorWindow!=None:
            self.theObjectEditorWindow.destroy()
        if self.theResultsWindow != None:
            self.theResultsWindow.deleted()
            self.theResultsWindow = None

    def createModel( self ):
        """ 
        in: nothing
        out nothing
        """
        if not self.closeModel():
            return False
        # create new model
        self.theModel = ModelStore( objs.Factory( self.theDMInfo ) )

        self.theLayoutManager = LayoutManager( self )
        self.theUndoQueue = CommandQueue(MAX_REDOABLE_COMMAND)
        self.theRedoQueue = CommandQueue(MAX_REDOABLE_COMMAND)
        
        # initDM

        # set name
        self.theModelName = 'Untitled'
        self.modelHasName = False
        self.changesSaved = True
        self.openLayoutWindow = False
        self.openObjectEditorWindow = False
        self.openConnObjectEditorWindow = False
        self.theLastComponent = None

        # init Autosave variables
        self.operationCount = 0
        self.theUpdateInterval = 0
        if self.theTimer != None:
            gtk.timeout_remove(self.theTimer)
            self.theTimer = None
            
        return True

    def loadRecentFileList( self ):
        """
        in: nothing
        returns nothing
        """
        self.theRecentFileList = []

        if os.path.isfile( config.recent_file_list_file ):
            # if exists open it
            aFileObject = open ( config.recent_file_list_file, 'r' )
            # parse lines
            aLine = aFileObject.readline()
            while aLine != '':
                self.theRecentFileList.append( aLine.strip( '\n' ) )
                aLine = aFileObject.readline()
            # close file
            aFileObject.close()

    def addToRecentFileList(self, aFileName ):
        """
        in: string aFileName (including directory, starting from root)
        returns nothing
        """
        # convert to absolute path
        if os.path.split(aFileName)[0] == '':
            aFileName = os.getcwd() + os.sep + aFileName

        # check wheter its already on list
        if aFileName in self.theRecentFileList:
            self.theRecentFileList.remove(aFileName )
            
        # insert new item as first
        self.theRecentFileList.insert ( 0, aFileName )

        # if length is bigger than max delete last 
        if len(self.theRecentFileList) > RECENTFILELIST_MAXFILES:
            self.theRecentFileList.pop()

        # save to file whole list
        self.saveRecentFileList()

    def getTmpDir(self):
        tmpDirPath = tempfile.gettempdir()
        return tmpDirPath

    def getEmlTmpFileName(self,  aFileName ):
        tmpFileBaseName = os.path.basename(aFileName)
        tmpName, tmpExt = os.path.splitext( tmpFileBaseName )
        return tmpName + '.eml'

    def saveRecentFileList( self ):
        """
        in: nothing
        returns nothing
        """
        # creates recentfiledir if does not exist
        aDirName = os.path.dirname( config.recent_file_list_file )
        if not os.path.isdir( aDirName ):
            os.mkdir( aDirName )
        # creates file 
        aFileObject = open( config.recent_file_list_file, 'w' )
        for aLine in self.theRecentFileList:
            # writes lines
            aFileObject.write( aLine + '\n' )
        # close file
        aFileObject.close()

    def convertPropertyValueList( self, aValueList ):
        aList = list()

        for aValueListNode in aValueList:

            if type( aValueListNode ) in (type([]), type( () ) ):

                isList = False
                for aSubNode in aValueListNode:
                    if type(aSubNode) in (type([]), type( () ) ):
                        isList = True
                        break
                if isList:
                    aConvertedList = self.convertPropertyValueList( aValueListNode )
                else:
                    aConvertedList = map(str, aValueListNode)

                aList.append( aConvertedList )
            else:
                aList.append( str (aValueListNode) )

        return aList

    def getUniqueName( self, aType, aStringList, prefix = "new" ):
        """
        in: string aType, list of string aStringList
        returns: string newName     
        """
        i = 1
        while True:
            # tries to create 'aType'1
            newName = prefix + aType + str(i)
            if newName not in aStringList:
                return newName
            # if it already exists in aStringList, creates aType2, etc..
            i += 1

    def plainMessage( self, theMessage ):
        """
        in: string theMessage
        returns None
        """

        print theMessage

    def loadStepper( self, anEml ):
        """stepper loader"""

        aStepperList = anEml.getStepperList()


        for aStepper in aStepperList:

            aClassName = anEml.getStepperClass( aStepper )
            self.theModel.createStepper( str( aClassName ),\
                str( aStepper ) )

            aPropertyList = anEml.getStepperPropertyList( aStepper )
            
            for aProperty in aPropertyList:

                aValue = anEml.getStepperProperty( aStepper, aProperty )
                self.theModel.loadStepperProperty( aStepper,\
                           aProperty,\
                           aValue )
                                             
    def loadEntity( self, anEml, aSystemPath='/' ):

        aVariableList = anEml.getEntityList( DM_VARIABLE_CLASS, aSystemPath )        
        aProcessList   = anEml.getEntityList( 'Process',   aSystemPath )
        aSubSystemList = anEml.getEntityList( 'System', aSystemPath )

        self.loadEntityList( anEml, 'Variable', aSystemPath, aVariableList )
        self.loadEntityList( anEml, 'Process',  aSystemPath, aProcessList )
        self.loadEntityList( anEml, 'System',   aSystemPath, aSubSystemList )

        for aSystem in aSubSystemList:
            aSubSystemPath = ecell.util.joinSystemPath( aSystemPath, aSystem )
            self.loadEntity( anEml, aSubSystemPath )

    def loadProperty( self, anEml, aSystemPath='' ):
        # the default of aSystemPath is empty because
        # unlike __loadEntity() this starts with the root system

        aVariableList  = anEml.getEntityList( 'Variable',  aSystemPath )
        aProcessList   = anEml.getEntityList( 'Process',   aSystemPath )
        aSubSystemList = anEml.getEntityList( 'System', aSystemPath )

        self.loadPropertyList( anEml, 'Variable',\
                         aSystemPath, aVariableList )
        self.loadPropertyList( anEml, 'Process',  aSystemPath, aProcessList )
        self.loadPropertyList( anEml, 'System',\
                         aSystemPath, aSubSystemList )

        for aSystem in aSubSystemList:
            aSubSystemPath = ecell.util.joinSystemPath( aSystemPath, aSystem )
            self.loadProperty( anEml, aSubSystemPath )

    def loadPropertyList( self, anEml, anEntityTypeString, aSystemPath, anIDList ):
        for anID in anIDList:

            aFullID = anEntityTypeString + ':' + aSystemPath + ':' + anID

            aPropertyList = anEml.getEntityPropertyList( aFullID )

            aFullPNList = map( lambda x: aFullID + ':' + x, aPropertyList )
            aValueList = map( anEml.getEntityProperty, aFullPNList )

            if MS_PROCESS_VARREFLIST in aPropertyList:
                idx = aPropertyList.index( MS_PROCESS_VARREFLIST )
                value = aValueList[idx]
                uniqueNameList = []
                for aVarref in value:
                    aName = aVarref[values.VARREF_NAME]
                    if aName in uniqueNameList:
                        newName = self.getUniqueName( "_", uniqueNameList, "" )
                        aVarref[values.VARREF_NAME] = newName
                        utils.showPopupMessage(
                            utils.OK_MODE,
                            "Ambigous variablereference for %s. " \
                            + "Old value %s changed to %s." % (
                                aFullPNList[idx], aName, newName),
                            ME_WARNING )
                        aName = newName
                    uniqueNameList.append( aName )


            map( self.theModel.loadEntityProperty,
                 aFullPNList, aValueList )

    def loadEntityList( self, anEml, anEntityTypeString, aSystemPath, anIDList ):
        aPrefix = anEntityTypeString + ':' + aSystemPath + ':'
        aMessage=''

        aFullIDList = map( lambda x: aPrefix + x, anIDList )
        aClassNameList = map( anEml.getEntityClass, aFullIDList )
        map( self.theModel.createEntity, aClassNameList, aFullIDList )

    def saveStepper( self , anEml ):
        """stepper loader"""

        aStepperList = self.theModel.getStepperList()

        for aStepper in aStepperList:

            aClassName = self.theModel.getStepperClassName( aStepper )
            anEml.createStepper( str( aClassName ), str( aStepper ) )

            aPropertyList = self.theModel.getStepperPropertyList( aStepper )

            for aProperty in aPropertyList:
                
                anAttributeList = self.theModel.getStepperPropertyAttributes( aStepper, aProperty)

                # check get attribute 
                if anAttributeList[MS_SAVEABLE_FLAG] and anAttributeList[MS_CHANGED_FLAG]:
                                    
                    aValue = self.theModel.saveStepperProperty( aStepper, aProperty )
                    if aValue == '' or aValue == []:
                        continue

                    aValueList = list()
                    if type( aValue ) != type([]):
                        aValueList.append( str(aValue) )
                    else:
                        aValueList = self.convertPropertyValueList( aValue )

                    anEml.setStepperProperty( aStepper, aProperty, aValueList )
    
    def saveEntity( self, anEml, aSystemPath='/' ):

        aVariableList = self.theModel.getEntityList(  'Variable', aSystemPath )
        aProcessList   = self.theModel.getEntityList( 'Process', aSystemPath )
        aSubSystemList = self.theModel.getEntityList( 'System', aSystemPath )
        
        self.saveEntityList( anEml, 'System',   aSystemPath, aSubSystemList )
        self.saveEntityList( anEml, 'Variable', aSystemPath, aVariableList )
        self.saveEntityList( anEml, 'Process',  aSystemPath, aProcessList )

        for aSystem in aSubSystemList:
            aSubSystemPath = ecell.util.joinSystemPath( aSystemPath, aSystem )
            self.saveEntity( anEml, aSubSystemPath )

    def saveEntityList( self, anEml, anEntityTypeString, aSystemPath, anIDList ):
        for anID in anIDList:
            aFullID = anEntityTypeString + ':' + aSystemPath + ':' + anID
            aClassName = self.theModel.getEntityClassName( aFullID )

            if aClassName == 'System::/':
                pass
            else:
                anEml.createEntity( aClassName, aFullID )

    def saveProperty( self, anEml, aSystemPath='' ):
        # the default of aSystemPath is empty because
        # unlike __loadEntity() this starts with the root system

        aVariableList  = self.theModel.getEntityList( 'Variable',\
                                                          aSystemPath )
        aProcessList   = self.theModel.getEntityList( 'Process',\
                                                          aSystemPath )
        aSubSystemList = self.theModel.getEntityList( 'System',\
                                                          aSystemPath )

        self.savePropertyList( anEml, 'Variable', aSystemPath, aVariableList )
        self.savePropertyList( anEml, 'Process', aSystemPath, aProcessList )
        self.savePropertyList( anEml, 'System', aSystemPath, aSubSystemList )

        for aSystem in aSubSystemList:
            aSubSystemPath = ecell.util.joinSystemPath( aSystemPath, aSystem )
            self.saveProperty( anEml, aSubSystemPath )

    def savePropertyList( self, anEml, anEntityTypeString, aSystemPath, anIDList ):
        for anID in anIDList:

            aFullID = anEntityTypeString + ':' + aSystemPath + ':' + anID
            aPropertyList = self.theModel.getEntityPropertyList( aFullID )

            for aProperty in aPropertyList:
                aFullPN = aFullID + ':' + aProperty
                
                anAttributeList = self.theModel.getEntityPropertyAttributes(aFullPN)

                # check savable
                if anAttributeList[MS_SAVEABLE_FLAG] and anAttributeList[MS_CHANGED_FLAG]:
                    aValue = self.theModel.saveEntityProperty(aFullPN)

                    if aValue != '' and aValue != []:

                        aValueList = list()
                        if type( aValue ) != type([]):
                            aValueList.append( str(aValue) )

                        else:
                            # ValueList convert into string for eml
                            aValueList = self.convertPropertyValueList( aValue )

                            
                        anEml.setEntityProperty( aFullID, aProperty, aValueList )
    
    def createAutosaveWindow(self, aDuration):
        anAutosaveWindow = AutosaveWindow.AutosaveWindow(self, aDuration)
        return anAutosaveWindow.return_result()
            
    def getAutosavePreferences( self ):
        AutosavePreferences = []
        AutosavePreferences.append( int( self.getParameter( 'duration' ) ) )
        AutosavePreferences.append( int( self.getParameter( 'operations' ) ) )
        return AutosavePreferences

    def setAutosavePreferences( self, AutosavePreferences ):
        """
        saves autosave preferences into config database
        """
        self.operationCount = 0
        self.theUpdateInterval = 0 
        if self.theTimer != None:
            gtk.timeout_remove( self.theTimer )
            self.theTimer = None
        self.setParameter( 'duration', AutosavePreferences[0] )
        self.setParameter( 'operations',AutosavePreferences[1] )
        self.saveParameters()

    def setParameter(self, aParameter, aValue):
        """tries to set a parameter in ConfigDB
        if the param is not present in either autosave or default section raises exception and quits
        """
        # first try to set it in autosave section
        if self.theConfigDB.has_section('autosave'):
            if self.theConfigDB.has_option('autosave',aParameter):
                self.theConfigDB.set('autosave',aParameter, str(aValue))
        else:
            # sets it in default
            self.theConfigDB.set('DEFAULT',aParameter, str(aValue))

    def saveParameters( self ):
        """tries to save all parameters into a config file in home directory
        """
        self.theIniFolderName = GUI_HOMEDIR + os.sep + '.modeleditor' + os.sep
        if os.path.isdir(self.theIniFolderName):
            try:
                fp = open( self.theIniFileName, 'w' )
                self.theConfigDB.write( fp )
            except:
                utils.showPopupMessage(
                    utils.OK_MODE,
                    "Could not save preferences into file %s.\n" \
                    + "Please check permissions for home directory.\n" % \
                        self.theIniFileName,
                    ME_ERROR )
        else:
            os.system('mkdir ' + self.theIniFolderName)
  
    def getParameter( self, aParameter ):
        """tries to get a parameter from ConfigDB
        if the param is not present in either autosave or default section
        raises exception and quits
        """

        # first try to get it from autosave section
        try:
            return self.theConfigDB.get( 'autosave', aParameter )
        except:
            # gets it from default
            return self.theConfigDB.get( 'DEFAULT', aParameter )
   
    def openConfirmWindow(self,  aMessage, aTitle, isCancel = 1 ):
        """ pops up a modal dialog window
            with aTitle (str) as its title
            and displaying aMessage as its message
            and with an OK and a Cancel button
            returns:
            True if Ok button is pressed
            False if cancel button is pressed
        """
        aConfirmWindow = ConfirmWindow( isCancel, aMessage, aTitle )
        return aConfirmWindow.return_result() == utils.OK_PRESSED

    def readIni(self,aPath):
        """read preferences.ini file
        an preferences.ini file may be in the given path
        that have an autosave section or others but no default
        argument may be a filename as well
        """

        # first delete every section apart from default
        for aSection in self.theConfigDB.sections():
            self.theConfigDB.remove(aSection)

        # gets pathname
        if not os.path.isdir( aPath ):
            aPath=os.path.dirname( aPath )

        # checks whether file exists
        aFilename=aPath+os.sep+ '.modeleditor' + os.sep + 'preferences.ini'
        if not os.path.isfile( aFilename ):
            # self.message('There is no preferences.ini file in this directory.\n Falling back to system defauls.\n')
            return None

        # tries to read file

        try:
            self.message('Reading preferences.ini file from directory [%s]' %aPath)
            self.theConfigDB.read( aFilename )

        # catch exceptions
        except:
            self.message( ' error while executing ini file [%s]' % aFileName )
            anErrorMessage = '\n'.join( traceback.format_exception( sys.exc_type,sys.exc_value,sys.exc_traceback ) )
            self.message( anErrorMessage )

    def printMessage( self, aMessageText ):
        if self.theMainWindow.exists():
            self.theMainWindow.displayMessage( aMessageText )
            self.theMainWindow.printOnStatusbar( aMessageText )
        else:
            print aMessage
