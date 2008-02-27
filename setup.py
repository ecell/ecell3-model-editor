#!/usr/bin/env python

import os
import sys
import ecell.config
from glob import glob
from distutils.core import setup, Extension

resources = glob(
    os.path.join( os.path.dirname( __file__ ), 'glade', '*' ) )

plugins = glob(
    os.path.join( os.path.dirname( __file__ ), 'plugins', '*' ) )

setup(
    name = 'ecell.model-editor',
    version = '3.1.106',
    description = 'E-Cell Model Editor',
    author = 'E-Cell project',
    author_email = 'info@e-cell.org',
    url = 'http://www.e-cell.org/',
    packages = [
        'ecell.ui',
        'ecell.ui.model_editor',
        'ecell.ui.model_editor.peer',
        'ecell.ui.model_editor.peer.canvas',
        'ecell.ui.model_editor.command',
        'ecell.ui.model_editor.shape',
        'ecell.ui.model_editor.shape.parts',
        'ecell.ui.model_editor.schematic'
        ],
    scripts = [ 'ecell3-model-editor' ],
    data_files = [
        ( ecell.config.conf_dir,
          [ 'model-editor.ini' ] ),
        ( os.path.join( ecell.config.data_dir,
            'model-editor', 'glade' ), resources ),
        ( os.path.join( ecell-config.lib_dir,
            'model-editor', 'plugins' ), plugins ),
        ]
    )
