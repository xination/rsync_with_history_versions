#!/usr/bin/python
import sys
import os
import rlcompleter
import readline  
import subprocess
from datetime import date
from datetime import timedelta
from docopt import docopt

 

######################################################
# the functions which invoke subprocess

def do_bash_read( ):
    cmd ="""./readIn.sh"""
    p = subprocess.Popen( cmd, shell=True,  stdout=subprocess.PIPE )  
    (results,err) = p.communicate()
    return results.strip()



def get_find_results( directory, option = "" ):
    cmd =""" find %s %s 2>/dev/null"""%( directory, option )
    p = subprocess.Popen( cmd, shell=True,  stdout=subprocess.PIPE )  
    (results,err) = p.communicate()
    results = results.split()
    return results


def do_ls( source, option = ""  ):
    # note: if source does not exist, this function returns an empty list.
    cmd =""" ls %s %s 2>/dev/null"""%( source, option )
    p = subprocess.Popen( cmd, shell=True,  stdout=subprocess.PIPE )  
    (results,err) = p.communicate()
    results = results.split()

    return results


def do_cp( sources, dir ):
    ''' input: sources is a list contains the files to be copied'''

    src_str = ""
    for source in sources: 
        src_str += source

    cmd = "cp -ar %s %s" %( src_str, dir )
    p = subprocess.Popen( cmd, shell=True,  stdout=subprocess.PIPE ) 


 
def do_rsync_dry_run( source, dirBackup ):
    ''' call rsync --dry-run 
        using "update" and "itemize-changes" options
    '''

    cmd =""" rsync --verbose --compress \
                   --archive --recursive \
                   --itemize-changes --delete \
                   --dry-run  --update %s %s 
    """%( source, dirBackup )
 
    p = subprocess.Popen( cmd, shell=True,  stdout=subprocess.PIPE )  
    (results,err) = p.communicate()
    results = results.split("\n") 
    results = results[1:-3]

    # remove empty elements
    temp = []
    for result in results:
        if result != "": temp.append( result)
    results = temp[:]
    del temp       
    return results


 
def do_rsync( source, dirBackup, port=22 , debug = False ):
     
    cmd = ""
    if( port == 22 ):
        # for local and ssh with normal port =22
        cmd =""" rsync --verbose --compress \
                       --archive --recursive \
                       --itemize-changes --delete \
                       --update %s %s 
        """%( source, dirBackup )
    else:
        # for ssh with port other than 22
        cmd =""" rsync --verbose --compress \
                 --archive --recursive \
                 --itemize-changes --delete \
                 -e "ssh -p %d -o 'ControlPath=$HOME/.ssh/ctl/%%r@%%h:%%p'" \
                 --update  %s %s 
        """%( port, source, dirBackup )    
    if( debug ): 
        print cmd
    else:     
        subprocess.check_call( cmd, shell=True,  stdout=subprocess.PIPE )
     

    
def do_cat( fName ):
    cmd =""" cat  %s """  %( fName )
    subprocess.check_call( cmd, shell=True  )



def getDateTime_info( ):
    cmd = 'date "+%Y%m%d%H%M"'
    p = subprocess.Popen( cmd, shell=True,  stdout=subprocess.PIPE )
    (dateTimeInfo,err) = p.communicate() 
    dateTimeInfo = dateTimeInfo.strip()
    return dateTimeInfo



def makePatch( old, new , patch_fileName ):
    # note -u option give us time stamp
    cmd = "diff -u %s %s > %s" %( old, new, patch_fileName )
    
    p = subprocess.Popen( cmd, shell=True,  stdout=subprocess.PIPE )
    (result,err) = p.communicate()
    

def isDifferent( old, new ):
    cmd = "diff -u %s %s" %( old, new )
     
    p = subprocess.Popen( cmd, shell=True,  stdout=subprocess.PIPE )
    (result,err) = p.communicate() 
     
    if result != "":
        return True
    else:
        return False


def getCurrentPath( ):
    # not in used now.
    cmd="pwd"
    p = subprocess.Popen( cmd, shell=True,  stdout=subprocess.PIPE )
    (result,err) = p.communicate() 
    currentPATH=result.strip()
    return currentPATH 



def getAbsolutePath( path ):
    # not in used now.
    # convert relative path to absolute path
    # it use 'dirname' and 'basename'
    cmd=""" echo "$(cd "$(dirname %s)"; pwd)/$(basename %s)"  """ \
         %( path, path)
    p = subprocess.Popen( cmd, shell=True,  stdout=subprocess.PIPE )
    (result,err) = p.communicate() 
    abs_path=result.strip()
    return abs_path 


#### the following functions do not have return

def applyPatch_Reverse( fName, patch_fName ):
    
    # option "--reject-file -" or "-r -" is to discard .rej files.
    cmd = "patch -r - -R --ignore-whitespace %s < %s " %(fName, patch_fName )
    
    p = subprocess.Popen( cmd, shell=True,  stdout=subprocess.PIPE )
    (result,err) = p.communicate()

    # print 'debug result = ', result 
    # print 'debug err = ', err 

   
    

def make_a_fold( folderName ):
    cmd = "mkdir -p %s" %( folderName )
    subprocess.check_call( cmd, shell=True,  stdout=subprocess.PIPE )

def remove_a_folder( folderName ):
    cmd = "rm -r %s" %( folderName )
    subprocess.check_call( cmd, shell=True,  stdout=subprocess.PIPE )
    pass


def do_touch( dateTime, fName ):
    # change modification time of a file
    cmd = "touch  -m -t %s %s" %( dateTime, fName )
    subprocess.check_call( cmd, shell=True,  stdout=subprocess.PIPE )
    pass

##### handy functions (no subprocess )

def get_fileName( _fPath ):
    # extract file name from a path
    
    if( _fPath.find("/") == -1 ):
        return _fPath

    N = len(_fPath)
    idx = 0 
    for i in range( len(_fPath) ):
        if( _fPath[ -N + i ] == '/' ):
            idx = i 
              
    return _fPath[ idx+1: ] 


def get_dirName( _fileName ):
     
    N = len(_fileName)
    idx = 0 
    for i in range( len(_fileName) ):
        if( _fileName[ -N + i ] == '/' ):
            idx = -N + i 
              
    return _fileName[ :idx ] 

#=======================================================================




class RSYNC( ):
    """ to use rsync to do back up and manage version history """
    
    def __init__( self ):
        
        # the backupDir is the topmost dir for backup
        # sources can be either dir or files.
        # they can be assigned by set_main_backup_folder 
        # and add_source methods
        self.backupDir = ""
        self.backupDir_remote=""
        self.port=22
        self.sources = []
        self.do_local = True
        self.do_remote = False

        self.upperDays = sys.maxint 
        # keep version upto XX days.
        # it can be changed by set_upper_days()

        # for processing
        self.modified_files = []
        self.modified_files2 = [] 
        self.deleted_files = []
        self.deleted_files2 = []
        self.history_versions = []
        self.dry_run_results = []

        # fixed dirname
        self.tempDir=".temp"        
        self.historyDir=".history"  
        pass


    def debug_run( self ):
        
        self.get_dry_run_result( debug = True )

        self.get_modified_files( debug = True )

        if( len( self.modified_files )>0 ):
            self.make_patches_for_modified_files( debug = True )  

        self.get_deleted_files( debug = True )        
        
        if( len( self.deleted_files ) > 0 ):
            self.archieve_deleted_files_entrieCopy( debug = True ) 

        self.manage_history_version( debug = True )


        if( self.do_local ):
            self.update_backupDir( "local", debug = True  )
            print "backup done" 
        
        
        if( self.do_remote ):
            self.update_backupDir( "remote", debug = True )
            print "backup remote done" 
            pass



    def process( self ):
        ''' the main backup process is done here'''
        
        self.get_dry_run_result(  ) 
        if len(self.dry_run_results) == 0 :
            print "up to date, no need to backup"
            return 

        self.get_deleted_files()  
        if( len( self.deleted_files ) > 0 ):
            self.archieve_deleted_files_entrieCopy()  

        self.get_modified_files()  
        if( len( self.modified_files )>0 ):
            self.make_patches_for_modified_files()  
        
        self.manage_history_version()

        if( self.do_local ):
            self.update_backupDir( "local" )
            print "backup done" 
        
        if( self.do_remote ):
            self.update_backupDir( "remote" )
            print "backup remote done" 
            pass
        pass

    ###################################################
    # methods related to user setting

    def __parse( self, line, key ):
        line = line.strip() 
        STATUSLEN = len(key) + 1
        item = line[ STATUSLEN+1: ] 
        item = item.strip()
        return item


    def read_in_backup_plan( self, backup_plan ):
        ''' read in a backup instruction and then process it '''
        
        with open(backup_plan, "r" ) as f:
            lines = f.readlines()

        for line in lines:
            if( line[0] == "#" or len(line) == 0 ) : continue

            if line.find( "local_backup_folder" ) != -1:
                self.backupDir = self.__parse( line, "local_backup_folder" )
                
            elif line.find( "remote_backup_folder" ) != -1:
                self.backupDir_remote = self.__parse( line, "remote_backup_folder" )
                 
            elif line.find( "ssh_port" ) != -1:
                self.port =  int( self.__parse(line, "ssh_port") ) 
                 
            elif line.find( "add_source" ) != -1 :
                self.add_source( self.__parse(line, "add_source") )
            
            elif line.find( "keep_version" ) != -1 :     
                duration = int( self.__parse(line, "keep_version") ) 
                self.upperDays = duration 
            
            elif line.find( "do_local_backup" ) != -1 :     
                flag = self.__parse(line, "do_local_backup") 
                if flag.lower() ==  "true":
                    self.do_local = True
                else:
                    self.do_local = False

            elif line.find( "do_remote_backup" ) != -1 :     
                flag = self.__parse(line, "do_remote_backup") 
                if flag.lower() ==  "true":
                    self.do_remote = True
                else:
                    self.do_remote = False
                  
        pass

 
    def add_source( self, fileName_path ):
        ''' add to self.sources'''
        self.sources.append( fileName_path )

    ###################################################
     

    def validate_fName_dateTime( self ):
        print "input filename [use tab to autocomplete]"
        while 1:
            fName = do_bash_read()
            fName = os.path.abspath( fName )
            if not os.path.exists( fName ):
                print " your input file does not exist"
            else:
                break


        versions = self.get_file_versions( fName )
        if( len(versions) == 0 ): return

        print "available time stamp: "
        for idx, v in enumerate( versions ): 
            print "%2d: %s" %( ( len(versions) - idx), self.convert_to_readable( v ) )
        
        while( 1 ):
            dateTime_idx = int( raw_input("select a timestamp: " ) )
            dateTime_idx = len(versions) - dateTime_idx
            # dateTime = self.convert_to_machine( dateTime)
            dateTime = versions[ dateTime_idx ]

            if dateTime not in versions:
                print "%s is not available for %s" \
                %( self.convert_to_readable( dateTime ), fName )
            else:
                break
        return fName, dateTime 


    def validate_fName_dateTime2( self ):
        ''' for deleted files '''
        historyDir = self.backupDir + "/" + self.historyDir + "/"
        results = get_find_results( historyDir, "-type f" )

        print "tip: use option 5 to see all the deleted files from previous history."
        
        notFound = True
        while 1:
            print "note: -1 to cancel"
            fName = raw_input("input deleted filename: ")
            
            if( fName[:2] == './' ): fName.replace("./", "" )
         
            available_dateTime = []
            for result in results:
                if result.find( fName) != -1:
                    notFound = False
                    dateTime = result.replace( historyDir ,"" )
                    dateTime = dateTime.split("/")[0]
                    available_dateTime.append( dateTime )
                    print "%s %s" \
                    %( self.convert_to_readable( dateTime), fName )
                  
            if notFound : 
                print "%s not in the deleted-file list" %(fName)
            else:
                break
        

       
        if( len(available_dateTime) == 1 ):
            fName = historyDir  + available_dateTime[0] + "/deleted/" + fName
            return fName 
        else:
            print "select time stemp: "

            for v in available_dateTime: 
                print self.convert_to_readable( v )
        
            while( 1 ):
                dateTime = raw_input("input time stamp: " )
                dateTime = self.convert_to_machine( dateTime )
                if dateTime not in available_dateTime:
                    print "%s is not available for %s" \
                    %( self.convert_to_readable( dateTime ), fName )
                else:
                    fName = historyDir  + available_dateTime[0] + "/deleted/" + fName
                    break
            return fName 


    def actions( self, opt ):
        if( opt.lower() == "xx" ):
            sys.exit(1) 

        elif( opt == "1" ):
            versions = self.get_history_versions()
            for v in versions: 
                print self.convert_to_readable( v )
        
        elif( opt == "2" ):
            
            print "input filename [use tab to autocomplete]"
            fName = do_bash_read()

            if not os.path.exists( fName ):
                print " your input file does not exist"
            else:
                versions = self.get_file_versions( fName )
                for v in versions: 
                    print self.convert_to_readable( v )
        
        elif( opt == "3" ):
             
            print "input filename [use tab to autocomplete]"
            while 1:
                fName = do_bash_read()
                fName = os.path.abspath( fName )
                if not os.path.exists( fName ):
                    print " your input file does not exist"
                else:
                    break
            versions = self.get_file_versions( fName )
            if( len(versions) == 0 ): return

            while ( 1 ):

                print "available time stamp: "
                for idx, v in enumerate( versions ): 
                    print "%2d: %s" \
                    %( ( len(versions) - idx), self.convert_to_readable( v ) )
                
                print "note:  -1 to exit"
                dateTime_idx = int( raw_input("select a timestamp: " ) )
                if dateTime_idx == -1: break 

                dateTime_idx = len(versions) - dateTime_idx
                dateTime = versions[ dateTime_idx ]
                if dateTime not in versions:
                    print "%s is not available for %s" \
                    %( self.convert_to_readable( dateTime ), fName )
                else:
                    self.view_previous_version( fName, dateTime )


        elif( opt == "4" ):
            (fName, dateTime) = self.validate_fName_dateTime()
            self.back_to_previous_version( fName, dateTime )

        elif( opt == "5" ):
            self.show_all_deleted_files( ) 

        elif( opt == "6" ): 
            fName = self.validate_fName_dateTime2()
            if( fName != 0   ):
                print "preview ", fName, ": "
                print "============== result:"
                do_cat( fName )

        elif( opt == "7" ): 
            fName = self.validate_fName_dateTime2()
             
            if( fName != 0   ):

                fName_source = fName.split( "/deleted/")[-1]
                
                source_dir = get_dirName( fName_source )
                 
                do_cp( fName, "/"+source_dir )
                print "recovery is done" 

         


        raw_input( "\npress any key to continue")
        os.system('clear');        

    def show_menu( self ):
        '''
        print the menu and then return the option.
        '''
        os.system('clear');
         
        strOut =""
        strOut+="""
    -----------------------------------------------------------
    (1) Show all time stamps
    (2) Show all time stamps for a given file
    (3) View a file by a time stamp
    (4) Roll back a file back to a time stamp
    (5) Show all deleted files from previous history 
    (6) View a deleted file 
    (7) Recover a deleted file.
    -----------------------------------------------------------
    (XX) Exit  

    Your choice:  """ 
        
        while (1):    
            opt = raw_input( strOut )
            self.actions( opt )      
           
        
         

    ###################################################
    # methods related to retrieve info
    

    def get_dry_run_result( self , debug = False ):
        ''' return is a list of abs path 
        '''
        
        if( debug ): print "inside get_dry_run_result "

        ## convert path to abs path, and store them into a list.
        source_tmp = []
        for source in self.sources:
            source_abs = os.path.abspath( source )
            if source_abs not in source_tmp: 
                source_tmp.append( source_abs )

        self.sources = source_tmp[:]


        ## check source with our local repo to see whether it is modified or not.
        for source in self.sources:

            if( debug ): print "source:", source

            dry_run_results = \
                do_rsync_dry_run( source, self.backupDir )
            
            # note: the filenames in the outcome of rsync dry run
            # are just tails, and so I convert them to abs path.
            item2 = ""
            for item in dry_run_results:
                if( debug ):
                    print "origin dry run result: ", item 

                if os.path.isfile( source ):
                    # source is a file.
                    
                    item2 = item + "|" + source

                    if (item2 not in self.dry_run_results ):
                        self.dry_run_results.append( item2 )
                    if( debug ): print "dry_run_result:", item2

                elif os.path.isdir( source ):
                    # source is a dir
                    
                    # this block is to handle the following stuff:
                    # from source=> /home/xination/data_temp          #dir
                    # from rysnc =>                data_temp/junk.txt #file
                    # we want    => /home/xination/data_temp/junk.txt #combined
                    
                    head, tail = os.path.split( source )
                     
                    item2 = item.strip() + "|" + head.strip() + "/" + item[ 12: ].strip()
                    if ( item2 not in self.dry_run_results  and len(item) != 0 ):
                        self.dry_run_results.append( item2 )

                    if( debug ): print "dry_run_result:", item2

             
        if( debug ): print "end\n"
        return self.dry_run_results


    def get_modified_files( self, debug = False ):
        ''' this function return a list containing the filenames for 
            modified files.
        '''
         
        ## warning message
        if self.backupDir == "":
            print "no backup folder is set"
            print "use set_main_backup_folder() "
            return 

        ## warning message    
        if len( self.sources ) == 0 :
            print "no source is set"
            print "use add_source() "
            return 

        STATUSLEN = 12
        for result in self.dry_run_results:
            if( result[:2] == ">f" and (result.find("+") == -1 ) ):
                filePath = result[ STATUSLEN: ] 
                (fTemp, absPath ) = filePath.split("|")
                
                if( absPath not in self.modified_files ):
                    self.modified_files.append(  absPath )
                    self.modified_files2.append( filePath )

        #---------------------------
        if( debug ):
            print "inside get_modified_files()"
            print "the following are modified files:"
            for item in self.modified_files:
                print "modified file:", item
            print "end\n"
        #---------------------------
             
        return self.modified_files
          

    def get_deleted_files( self , debug=False):
        ''' this function return a list containing the filenames for 
            deleted files.
        '''
        ## warning message
        if self.backupDir == "":
            print "no backup folder is set"
            print "use set_main_backup_folder() "
            return 

        ## warning message    
        if len( self.sources ) == 0 :
            print "no source is set"
            print "use add_source() "
            return 

        STATUSLEN = 12    
        for result in self.dry_run_results:
            if(  result.find("deleting") != -1  ):
                filePath = result[ STATUSLEN: ] 
                ( fDelete ,absPath ) = filePath.split("|")
                
                if( absPath not in self.deleted_files ):
                    self.deleted_files.append( (fDelete ,absPath )  )
                 


        #---------------------------
        if( debug ):
            print "inside get_deleted_files()"
            print "TEST backupDir = ", self.backupDir
            print "TEST sources ", self.sources
            print "The following are deleted files:"
            for item in self.deleted_files:
                print "deleted_file:", item
            print "end\n"
        #---------------------------


        return  self.deleted_files
       
 
     



    ###################################################
    # methods related to do archieve and patch  


    def update_backupDir( self, flag, debug = False ):
         
        if( flag == "local" and not debug ):
            src = ""
            for source in self.sources:
                src += source + " "
            do_rsync( src, self.backupDir, port=22, debug=debug ) 

        if( flag == "remote" and not debug ):    
            do_rsync( self.backupDir + "/" , self.backupDir_remote, port=self.port, debug=debug )
        
        if( debug ):
            print "in debug mode: update_backupDir() will do nothing."


    def archieve_deleted_files_entrieCopy( self, debug = False ):
        ''' to backup the deleted files 
            we will make a local copy first, then push to remote.
        '''
        
        deletedFolder = self.backupDir + "/" + self.historyDir + "/" + \
                        getDateTime_info() + "/deleted"
        
        if( debug):
            print "inside archieve_deleted_files_entrieCopy()"
            print "deletedFolder:", deletedFolder
            print "=> copy deleted files to deletedFolder"


        for source in self.deleted_files:
            ( fDelete, absPath ) = source
            dirName = get_dirName( deletedFolder + absPath )
            
            src = self.backupDir + "/" + fDelete    
            
            if( debug ):
                print "we create a folder:", dirName
                print "copied file:", src
            else:
                make_a_fold( dirName )
                do_cp( src, dirName )

        if( debug): print "end\n"
          
        
        pass


    def archieve_modified_files_entrieCopy( self ):
        ''' currently not in used...''' 
        archiveFolder = self.backupDir + "/" + self.historyDir + "/" + \
                        getDateTime_info() + "/changed/"
        
        make_a_fold( archiveFolder )                
        src = ""
        for source in self.modified_files:
            src += self.backupDir+"/"+ source + " "
        
        do_rsync( src, archiveFolder )    
        pass


    def make_patches_for_modified_files( self, debug = False ):
        ''' we will make patch files 
        '''
        # note: rsync uses modified date to compare
        # so even the content doesn't change, it is possible
        # to be considered changed file.


        patchFolder = self.backupDir + "/" + self.historyDir + "/" + \
                        getDateTime_info() + "/patch"
        
        if( debug ):
            print "inside make_patches_for_modified_files()"
            print "patchFolder:", patchFolder

        for absPath, filePath in \
                zip( self.modified_files, self.modified_files2):
            
            sourceN = filePath.split("|")[0]
            old_file = self.backupDir+ "/" +  sourceN  
            new_file = absPath 
            path_file = patchFolder + absPath + ".patch"
            dirName = get_dirName( patchFolder + absPath )
            
            if( debug ):
                print  "old=", old_file, \
                       "new=", new_file, \
                       "pathfile:" , path_file
                       # "dirName=", dirName, "\n"
            
            # when debug flag is active, we will enter the loop.            
            if( isDifferent( old_file, new_file ) and not debug ): 
                make_a_fold( dirName )
                makePatch( old_file, new_file , path_file )

                
        if( debug ): print "end\n"
        pass


    ###################################################
    # methods related to modified files


    def get_file_versions( self, fName ):
        ''' given a file name, it returns modifying history ''' 
        
        if( fName[:2] == "./" ):
            fName = fName[2:]

        # check input 
        if len( do_ls(fName ) )== 0:
            print "cannot find %s" %fName
            return 

         
        historyDir = self.backupDir + "/" +  self.historyDir
        results = get_find_results( historyDir ) 
         
        idx1 = len( historyDir) + 1
        idx2 = idx1 + 12 
        versions = []
        for result in results:
            if( result.find( fName) != -1 and result.find( "patch") != -1 ):
                dateTime = result[ idx1 : idx2 ]
                versions.append( dateTime )
                
        if( len(versions) == 0  ):
            print "no previous record"
            return []

        # sort
        versions.sort( reverse=False )
        
        return versions


    def get_versions_short( self, fName, dateTime, toPrint=True ):
        '''  extract the subset of patch files, which can 
            recover fName to version of dateTime
        '''

        versions = self.get_file_versions( fName )  
         
        # check the input
        inputCorrect=False
        for version in versions:
            if dateTime == version:
                inputCorrect = True

        if( inputCorrect == False ): 
            print "%s is not available" %( dateTime )
            return []
        else:
            if( toPrint ):
                for ii in range( len(versions) ):
                     
                    if( dateTime == versions[ii] ):
                        pass
                        print "%s <== selected" %( dateTime )
                    else:
                        print versions[ii]
         

        # get the shortened versions
        versions_short = []
        toBreakNextTime = False
        for version in versions:
            if( dateTime != version ):
                versions_short.append( version )
            elif( dateTime == version ):
                toBreakNextTime = True

            if( toBreakNextTime ): break

        return versions_short
        

    def back_to_previous_version( self, fName, dateTime, debug = False ):
        # todo: remove debugFlag. we will create testing function
        # somewhere else.

      

        versions_short = self.get_versions_short( fName, dateTime, False )
        
        if( len(versions_short) == 0 ): return

  
        
        print "Current: "
        do_cat( fName )   
         
        
        # apply patches   
        patchName = "" 
        for version in versions_short:
            
            patchName = self.backupDir + "/" + self.historyDir + "/" \
                + version + "/patch/" +  fName + ".patch"

            if( debug ):     
                print "-----------------------"   
                print "patch version = ", version  
             
                     
            applyPatch_Reverse( fName, patchName )
            
            if( debug ): 
                print "after apply %s" %version  
                do_cat( fName )                  

        print "roll back to %s: " % self.convert_to_readable( version )         
        do_touch( dateTime, fName ) # change the modification time.  
        do_cat( fName )
        pass




         

    def view_previous_version( self, fName, dateTime, debug=False ):

         
        versions_short = self.get_versions_short( fName, dateTime, True )

        
        # clean the old temp working folder (seems not necessary)    
        # dirToRemove = self.backupDir + "/" + self.tempDir 
        # remove_a_folder( dirToRemove )

        # make a temp working folder
        tempDir = self.backupDir + "/" + self.tempDir 
        make_a_fold( tempDir )

        # make a copy  
        do_rsync( fName, tempDir )
       
        # deal with file name
        fNameTemp = get_fileName( fName )
        fNameTemp = self.backupDir + "/" + self.tempDir + "/" + fNameTemp
        fNameTemp = fNameTemp.replace("//","/")
        if( debug ):
            print "-----------------------"   
            print "latest version"            
            do_cat( fNameTemp )               

        # apply patches        
        for version in versions_short:
            
            patchName = self.backupDir + "/" + self.historyDir + "/" \
                + version + "/patch/" +  fName + ".patch"

            if( debug ):    
                print "-----------------------"  # for debug
                print "patch version = ", version
                print "debug fNameTemp = ", fNameTemp
                    
            applyPatch_Reverse( fNameTemp, patchName )
            
            if( debug ):    
                print "after apply %s" %version 
                do_cat( fNameTemp ) #for debug

        # print on the screen.    
        print "==================== preview result:"
        do_cat( fNameTemp )    
        pass    
         
    ###################################################
    # methods related to deleted files.

    def show_all_deleted_files( self ):
        ''' print out all deleted files in backup/history/version/deleted/ '''
        historyDir = self.backupDir + "/" + self.historyDir + "/"
        results = get_find_results( historyDir, "-type f" )
        
        iFile = 0
        for fName in results:
            if( fName.find("deleted/") != -1 ):
                fName = fName.replace( historyDir ,"" )
                fName = fName.replace( "/deleted/" ," " )
                
                dateTime = fName.split()[0]
                dateTime = self.convert_to_readable( dateTime )
                fName = fName.split()[-1]
                iFile += 1 
                print "%2d: %s: %s" %(iFile, dateTime, fName )
        pass        

     

 
    ###################################################
    # methods for history versions


    def convert_to_machine( self, version ):
        return version.replace(",","" )    
        
    def convert_to_readable( self, version ):
        return version[:4] + "," + version[4:8] + "," + version[8:]

    def get_history_versions( self ):
        ''' get all the dirnames (dateTime) under history dir''' 
        historyDir = self.backupDir + "/" + self.historyDir + "/"
        self.history_versions = do_ls( historyDir ) 
        self.history_versions.sort( reverse=False )
        return self.history_versions

    def manage_history_version( self, debug = False ):
        
        self.get_history_versions()
        
        today = date.today()

        if( debug ): print "inside manage_history_version()"
             

        for version in self.history_versions:
            year   = int( version[  :4] )
            month  = int( version[ 4:6] ) 
            day    = int( version[ 6:8] )
            hour   = int( version[ 8:10] )
            minute = int( version[ 10:12] )
            version_pretty= "%d,%s,%d%d" %(year,version[4:8], hour,minute)
            version_date = date( year, month, day )
            deltaTime = abs( today - version_date )
            deltaTime_days = deltaTime.days
            
            if( debug ): print "version: ", version_pretty,\
                    "days:", deltaTime_days

            if ( self.upperDays < deltaTime_days ):
                dirName = self.backupDir + "/" + self.historyDir + "/" + version
                remove_a_folder( dirName )
                if( debug ): print "remove folder: %s" %(dirName)
            
            pass
        if( debug ): print "end\n"




__doc__= """RSYNC_BACKUP  

Usage:  script.py [-r BACKUP_PLAN     ] 
                  [-b MAIN_BACKUP_DIR ]   
                  [-hvid]   

Options:
    -h --help                Show this screen
    -v --version             Show version.
    -r --read BACKUP_PLAN    Read in a backup plan, and process it. 
    -i --interactive
    -d --dry-run
    
    example
    # process a backup plan
    ./script -r backup_plan

    # process a backup plan, and then go in interaction menu.
    ./script -ir backup_plan    

    # just do dry run    
    ./script -dr backup_plan 
"""

if __name__ == '__main__':
    
    rsync_tool = RSYNC()

    

    arguments = docopt(__doc__, version='RSYNC_BACKUP1.2' )
    # print("\n this is the arumgents from docopt:\n",  arguments )
     
    # process a backup plan
    if( len(sys.argv) == 1  ):
        print """ usage:
    ./script -r backup_plan

    # process a backup plan, and then go in interaction menu.
    ./script -ir backup_plan    

    # just do dry run    
    ./script -dr backup_plan 
        """
    elif( arguments['--dry-run'] ):
        rsync_tool.read_in_backup_plan( arguments['--read'] ) 
        rsync_tool.debug_run()

    elif( arguments['--read'] and arguments['--interactive'] ):
        # not finish yet.
        rsync_tool.read_in_backup_plan( arguments['--read'] )
        rsync_tool.process()
        rsync_tool.show_menu()
        
    elif( arguments['--read'] ):
        rsync_tool.read_in_backup_plan( arguments['--read'] )
        rsync_tool.process()

    
    
 
