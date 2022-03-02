#!/usr/bin/env python3
from cgi import test
from distutils.log import debug
from operator import truediv
from telnetlib import NOP
from tkinter import FALSE, Y
from pydactyl import PterodactylClient
from pathlib import Path
from tqdm import tqdm
from urllib.parse import urlparse
from config import *
import getpass
import requests
import logging
#import paramiko
import argparse
import yaml
import validators
import sys, os
import gettext
import keyring

#DO NOT EDIT -- SEE config.py for editable parameters.

_ = gettext.gettext
class rpConnection:    
    
    def __init__(self, instance:str, authbearer:str):
        self._instance = instance
        self._authbearer = authbearer        
        self._client = PterodactylClient(instance,authbearer)
    
    def check(self):    
        try:
            servers = self._client.client.servers.list_servers()
        except Exception as e:
            return e
        else:
            return True
    
    def server_exists(self, serverid: str):
        try:
            server = self._client.client.servers.get_server(serverid)
        except Exception as e:
            return e
        else:
            return True
    
    def get_client(self):
        return self._client
    
    def get_instance_url(self):
        return self._instance

    def get_full_authbearer(self):
        return self._authbearer





    def __repr__(self):
        return "{}({}, {})".format(self.__class__.__name__,self._instance, self._authbearer)


            
class rpServer:
    
    def __init__(self, identifier:str):

        self.identifier = identifier
        self.uuid = None
        self.name = None
        self.state = None
        self.pluginlist = None
        self.logger = logging.getLogger('rustplugins.server')
        self.pbar = None
        self.pbarfile=None
        self.ftpuser = None        
        
    
    def fetch(self, connection:rpConnection):
        
        if connection.check() != True:
            self.logger.info("Connection check to {} failed.".format(connection.get_instance_url))
            return None
        server = connection.get_client().client.servers.get_server(self.identifier)
        self.uuid = server['uuid']
        self.name = server['name']
        _util = connection.get_client().client.servers.get_server_utilization(self.identifier)
        self.state = _util['current_state']
    #region rp specific
       


    def console_command(self, connection:rpConnection, command:str):
         return connection.get_client().client.servers.send_console_command(self.identifier, command)
    
    def file_upload(self, connection:rpConnection, file:str) -> requests.Response:        
        # headers = {
        # 'Accept': 'application/json',
        # 'Content-Type': 'application/json',
        # 'Authorization': 'Bearer {}'.format(connection.get_full_authbearer()),
        # }        
        # uri = '{}/api/client/servers/{}/files/upload'.format(connection.get_instance_url(),self.identifier)
        # signeduirresp = requests.get(uri, headers=headers)
        # posturi = signeduirresp.json()['attributes']['url'] 
        
        posturi = connection.get_client().client.servers.files.get_upload_file_url(self.identifier)


        if os.path.exists(file):            
            files = {'files': open(file, 'rb')}
                
        uploadheaders = {'Content-Type': 'application/octet-stream'}
        r = requests.post(posturi, files=files)
                         
        if not r.ok:
            self.logger.debug(_("Error in {}.".format(__name__)))                          
            self.logger.debug(_("Req Uri: {}".format(r.request.url)))
            self.logger.debug(_("Req Headers: {}".format(r.request.headers)))
            self.logger.debug(_("Req Body: {}".format(r.request.body)))
            self.logger.debug(_("Resp Status: {}".format(str(r.status_code))))
            self.logger.debug(_("Resp Text: {}".format(r.text)))
      

        return r


    def file_rename(self, connection:rpConnection, source:str, dest:str) -> requests.Response:
        headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(connection.get_full_authbearer()),
        }
        uri = '{}/api/client/servers/{}/files/rename'.format(connection.get_instance_url(),self.identifier)
        payload = {
            'root': '/',
            'files': [
                {
                    'from': source,
                    'to': dest,
                },
            ],
        }
    
        r = requests.put(uri, json=payload, headers=headers)

        if not r.ok:
            self.logger.debug(_("Error in {}.".format(__name__)))                          
            self.logger.debug(_("Req Uri: {}".format(r.request.url)))
            self.logger.debug(_("Req Headers: {}".format(r.request.headers)))
            self.logger.debug(_("Req Body: {}".format(r.request.body)))
            self.logger.debug(_("Resp Status: {}".format(str(r.status_code))))
            self.logger.debug(_("Resp Text: {}".format(r.text)))
      

        return r
    
    def file_delete(self, connection:rpConnection, remotefile:str):
        connection.get_client().client.servers.files.delete_files(self.identifier,[remotefile])


    def file_details(self, connection:rpConnection, remotepath:str) -> requests.Response:
        headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(connection.get_full_authbearer()),
        }
        uri = '{}/api/client/servers/{}/files/list'.format(connection.get_instance_url(),self.identifier)
        
        params = {'directory': remotepath}
        self.logger.debug("params: {}".format(params))
        r = requests.get(uri, headers=headers, params=params)        

        if not r.ok:
            self.logger.debug(_("Error in {}.".format(__name__)))                          
            self.logger.debug(_("Req Uri: {}".format(r.request.url)))
            self.logger.debug(_("Req Headers: {}".format(r.request.headers)))
            self.logger.debug(_("Req Body: {}".format(r.request.body)))
            self.logger.debug(_("Resp Status: {}".format(str(r.status_code))))
            self.logger.debug(_("Resp Text: {}".format(r.text)))
      

        return r
    
        
    def file_detail(self, connection:rpConnection, remotefile:str):
        fpath,fname = os.path.split(remotefile)
        

     
        listresp = self.file_details(connection, fpath)
        if listresp:       
            jsondata = listresp.json()            
            
            for i in jsondata['data']:
                if i['attributes']['name'] == fname:
                    self.logger.debug(_("Found Item type {}".format(type(i['attributes']))))
                    self.logger.debug(_("Found Item {}".format(i['attributes'])))
                    return i['attributes'], listresp

        else:
            return None, listresp

        

    #region - disabled sftp functionality

    # def sftp_set_auth(self,user:str):
    #     self.ftpuser = user
    # def sftp_auth_exists(self):
    #     if self.ftpuser:
    #         return self.ftpuser
    #     else:
    #         return False
        

    # def sftp_check_auth(self,content:str, connection:rpConnection, password:str):
    #     fn = Path(self._sftp_writetestfile(content))
    #     return self.sftp_upload_file(self.ftpuser,password, fn, fn.name, connection)

    # def sftp_get_details(self, connection:rpConnection):
    #     details = connection.get_client().client.get_server(self.identifier)['sftp_details']
    #     return [details['ip'],details['port']]
    
    
    
    # def sftp_upload_file(self, username:str, password:str, file:Path, remotepath:str, connection:rpConnection):
    #     self._sftp_processupload(str(file.absolute()))
    #     s = os.path.getsize(str(file.absolute()))
    #     a = self.sftp_get_details(connection)[0]
    #     p = self.sftp_get_details(connection)[1]
    #     t = paramiko.Transport((a,p))
    #     try:
    #         t.connect(username=username,password=password)
    #         sftp = paramiko.SFTPClient.from_transport(t)
    #     except Exception as e:
    #         self.pbar=None
    #         t.close()
    #         self.logger.error(e)
    #         return
                            
    #     self.pbarfile = file.name
    #     try:                    
    #         r = sftp.put(str(file.absolute()),"{}/{}".format(remotepath,file.name),self._sftp_progress, True)
    #         sftp.chmod("{}/{}".format(remotepath,file.name), 644)
    #         sftp.chown("{}/{}".format(remotepath,file.name), 0,0)            
    #     except Exception as e:
    #         self.pbar=None
    #         t.close()
    #         self.logger.error(e)
    #         return
    #     else:
    #         if self.pbar.last_print_n < s:
    #             print(self.pbar.last_print_n)
    #             self._sftp_progress(r.st_size, r.st_size)
    #             self.pbar.close()
    #         t.close()
    #         self.pbar=None
    #         return  #r.st_size

    # def _sftp_progress(caller,transferred, total):
    #     if(caller.pbar):
    #         caller.pbar.n = int(transferred/1000)
    #         caller.pbar.update()
    #     else:
    #         caller.pbar = tqdm(range(int(total/1000)),'Uploading {}'.format(caller.pbarfile),unit='kb', position=0, leave=True,miniters=1)
    #         caller.pbar.n = int(transferred/1000)
    #         caller.pbar.update()

    # def _sftp_processupload(self, path:str):     
    #     with open(path, 'rb') as open_file:
    #      content = open_file.read()
        
    #     content = content.replace(b'\r\n', b'\n')
    #     content = content.replace(b'\r', b'\n')

    #     with open(path, 'wb') as open_file:
    #         open_file.write(content)

    # def _sftp_writetestfile(caller, content:str):
    #     fd,path = tempfile.mkstemp()
    #     with os.fdopen(fd,'w') as f:
    #         f.write(content)
    #         f.close             
    #     return path
    #endregion
    
    def pluginreload(self, connection:rpConnection, pluginfilename:str):
        self.logger.debug("plugin file {}".format(pluginfilename))
        reloadname = os.path.splitext(pluginfilename)[0]        
        self.logger.info(_("Attenpting automatic reload of plugin {}...".format(reloadname)))
        cmdresp = self.console_command(connection,"oxide.reload {}".format(reloadname))
        if(cmdresp.ok):
            self.logger.info(_("Umod plugin {} successfully locded on server.".format(pluginfilename)))
        else:
            self.logger.info(_("Umod plugin {} successfully loaded on server you may need to issue, but you will need to issue oxide.reload {} as we weren't able to.".format(pluginfilename,args.umod)))

    def pluginexists(self, connection:rpConnection, remotepath:str) -> bool:
        if remotepath:
            res,resp = self.file_detail(connection,remotepath)
            if res:
                return True
            else:
                return False
        else:
            return False


    def uploadplugin(self, connection:rpConnection, localpath:str, remotepath:str, overwrite:bool):
        ok = False
        
        errors = []
        localname = os.path.split(localpath)[1]                          
        uploadresp = self.file_upload(connection,localpath)
        if not uploadresp.ok:
            errors.append((_("File upload failed with {}\n".format(uploadresp.text))))
        else:
            self.logger.info(_("Uploaded to instance, moving..."))
            renameresp = self.file_rename(connection,localname, remotepath)                                            
            if(not renameresp.ok):                                                                                        
                if renameresp.json():
                    errdetail = renameresp.json()['errors'][0]['detail']                                            
                    if "Cannot move or rename file, destination already exists" in errdetail:                            
                            if overwrite:
                                self.file_delete(connection,  remotepath)
                                renameresp = self.file_rename(connection, localname, remotepath)                                            
                                if(not renameresp.ok):
                                    errors.append(_("Deleted {} however the move still failing with {}, Detail: {}.\n".format(localname,renameresp.text, errdetail)))
                                else:
                                    self.logger.info(_("Move success, reloading..."))
                                    self.pluginreload(connection, localname)
                                    ok = True
                                    return ok, errors                                    
                            else:
                                errors.append("PLugin exists but overwrite is not true, skipping.")

                    else:
                        errors.append(_("File move failed with {}, Detail: {}.\n".format(renameresp.text, errdetail)))
                        
            else:
                self.logger.info(_("Move success, reloading..."))
                self.pluginreload(connection, localname)
                return ok, errors
            return ok, errors

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__,self.identifier)



        
class rpConfig:
    yamlconfig = None    
    def write_config(self, configfile:str):
        with open(configfile, 'w') as file:
            yaml.dump(rpConfig.yamlconfig, file)
    def read_config(self, configfile: str):
        if os.path.exists(configfile):
            with open(configfile) as config:
                rpConfig.yamlconfig = yaml.load(config, Loader=yaml.Loader)                           
        else:
            rpConfig.yamlconfig = rpConfig.generate_config()
        if rpConfig.yamlconfig is not None:
            return rpConfig.yamlconfig
        else:
            rpConfig.yamlconfig = rpConfig.generate_config()
            return rpConfig.yamlconfig

    def generate_config():
        return {'config':'rustpluginsv1','remoteoxideplugins':'oxide/plugins','instance':'','lang':'en','serverlist':[]}

    def check_config_instance(self,):
        if rpConfig.yamlconfig is not None:
            if(rpConfig.yamlconfig['instance'] and rpConfig.getsecure('bearer')):
                return True
            else:
                return False
        else:
            return False
    def server_ismanaged(self, identifier:str):
        if len(rpConfig.yamlconfig['serverlist']) > 0:
            for server in rpConfig.yamlconfig['serverlist']:
                if server.identifier == identifier:
                    return True
        return False
    def server_getmanaged(self, identifier:str) -> rpServer:
        if len(rpConfig.yamlconfig['serverlist']) > 0:
            for server in rpConfig.yamlconfig['serverlist']:
                if server.identifier == identifier:
                    return server
        return False
    def setsecure(key:str,data:str):
        keyring.set_password(appname,"{}-{}".format(appkey,key),data)

    def getsecure(key:str):
        return keyring.get_password(appname,"{}-{}".format(appkey,key))
                    

class rpUtil:

    def https_download_file(url,destpath):        
        # Streaming, so we can iterate over the response.
        filename = os.path.basename(urlparse(url).path)
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            total_size_in_bytes= int(response.headers.get('content-length', 0))
            block_size = 1024 #1 Kibibyte
            progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
            with open(os.path.join(destpath,filename), 'wb') as file:
                for data in response.iter_content(block_size):
                    progress_bar.update(len(data))
                    file.write(data)
                file.close()
            progress_bar.close()
            if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
                print("ERROR, something went wrong")
            else:
                return True
        except requests.exceptions.RequestException as e:
            return e
    
    def file_isnt_zero(filepath:str):
            if os.path.isfile(filepath):
                if os.path.getsize(filepath) > 0:
                    return True
                else:
                    return False
            else:
                return True


        
            

    


parser = argparse.ArgumentParser(description=_('Manage rust plugins on rust instances within pterodactyl.'))
parser.add_argument('-i','--instance', nargs=2, metavar=('instance-uri','instance-bearer'), help=_('Configure connection to instance with uri and api key (bearer)'))
parser.add_argument('-s','--show-instance', action='store_true', help=_('Show connection to instance with uri and partial api key (bearer)'))
parser.add_argument('-t', '--list-available',action='store_true', help=_('List all servers available to manage'))
parser.add_argument('-L','--slist', action='store_true', help=_('List Managed Servers'))
parser.add_argument('-A','--sadd', metavar='<Server ID>', help=_('Add a server to manage.'))
parser.add_argument('-R','--sremove', metavar='<Server ID>', help=_('Remove a currently managed server.'))
parser.add_argument('-M', '--smanage', metavar='<Server ID>', help=_('Manage server with -u/-g/-p/-r'))
parser.add_argument('--force', action='store_true', help=_('Can be combined with --sremove to force removal of server.'))
parser.add_argument('-v','--verbose', action='store_true', help=_('Verbose mode. Print debugging messages about progress and process.'))

group = parser.add_mutually_exclusive_group()
group.add_argument('-l','--list', action='store_true', help=_('List maintained plugins.'))
group.add_argument('-u','--umod', metavar='umod-fikename', help=_('Install and Maintain Umod Plugin.'))
group.add_argument('-g','--gen', nargs=2, metavar=('gen-filename','gen-url'), help=_('Install and Maintain Generic Plugin.'))
group.add_argument('-p','--update', action='store_true', help=_('Update currently maintained plugins, Individual plugin if name specified.'))
#group.add_argument('-d','--individual', metavar='filename', help=_('Update individual plugin.'))
group.add_argument('-r', '--remove', help=_('Remove currently maintained plugin.'))
group.add_argument('-f', '--ftpauth', metavar='ftp-user', help=_('Set FTP Authentication Details prompting for password.'))
args = parser.parse_args()


#configuration vars - do not edit - see config.yaml after first run
#config.yaml location is specified by config.py in this directory, and defaults the same directory as this script.l
appname="rustplugins"
appfile = (Path(sys.argv[0]).name)
approot = str(Path(sys.argv[0]).parent.absolute())

#paths
#configuration
if os.path.isabs(configname):
    configfile = configname
else:
    configfile = os.path.join(approot,configname)
#cache directory
if os.path.isabs(cachedirname):
    cachedir = cachedirname
else:
    cachedir = os.path.join(approot, cachedirname)
#log    
if os.path.isabs(logname):
    logfile = logname
else:
    logfile = os.path.join(approot,logname)

#config objects
config = rpConfig()
config.read_config(configfile)

#directory structure
if not os.path.isdir(cachedir):
    try:
        os.mkdir(cachedir)
    except Exception as e:
        print(_("Directory Structure setup failed creating {}").format(cachedir))


#logging
logger = logging.getLogger(appname)
logger.setLevel(logging.DEBUG)
lstdout = logging.StreamHandler(sys.stdout)
lstdout.setLevel(logging.INFO)
lfile = logging.FileHandler(logfile)
lfile.setLevel(logging.DEBUG)
logger.addHandler(lfile)
logger.addHandler(lstdout)


# set current language
if config.yamlconfig is not None:
    lang_translations = gettext.translation('base', localedir='{}/locales'.format(approot), languages=[config.yamlconfig['lang']])
else:
    lang_translations = gettext.translation('base', localedir='{}/locales'.format(approot), languages=['en'])

lang_translations.install()
# define _ shortcut for translations
_ = lang_translations.gettext







#connection


if(config.check_config_instance()):
    basecon=rpConnection(config.yamlconfig['instance'], rpConfig.getsecure('bearer'))
else:    
    if not args.instance and len(sys.argv) > 1:    
        parser.error(_("-i/--instance configuration is required before using other features of {}").format(appfile))
    if len(sys.argv)  == 1:
        parser.print_help()

#operations

if(args.verbose):
    logging.getLogger(appname).setLevel(logging.INFO)
    
if(args.instance):
    print(_("Validating instance-uri {}.").format(args.instance[0]))
    print(_("Note: This tool uses your operating systems keyring to store your sensitive authentication data.\nYou may be asked for your keyring passord or to set one."))
    if(validators.url(args.instance[0])):
        if(config.yamlconfig['appkey'] == 'changeme'):
            print(_("You must change the application key from the default in config.py."))
        
            sys.exit()
        config.yamlcon
        fig['instance'] = args.instance[0]
        #config.yamlconfig['bearer'] = args.instance[1]        
        rpConfig.setsecure('bearer',args.instance[1])
        
        print(_("Validating instance-bearer {}.").format(rpConfig.getsecure('bearer')))
        con = rpConnection(config.yamlconfig['instance'], rpConfig.getsecure('bearer'))
        e = con.check()
        if not e == True:
            parser.error(_('Connection failure, double check uri and more importantly bearer.\nDetail: {}.').format(e))
        else:
            print(_("instance-uri and instance-bearer pass connection test."))
            print(_('Writing configuration to {}...').format(str(configfile)), end='')
            config.write_config(configfile)
            print(_("...done"))
            basecon = con

    else:
        parser.error(_("instance-uri is not a valid uri."))

if(args.show_instance):
    print(_("{} - Currently configured instance.\nuri: {}\npartial bearer: {}").format(appfile, config.yamlconfig['instance'], rpConfig.getsecure('bearer')[:16] ))

    
if(args.list_available):
    if not basecon.check() == True:
        basecon = rpConnection(config.yamlconfig['instance'], rpConfig.getsecure('bearer'))    
    print(_('{} - Available Servers:').format(appfile))
    client_servers = basecon.get_client().client.list_servers().data['data']    
    for server in client_servers:
        cs_attr = server['attributes']
        server_util = basecon.get_client().client.get_server_utilization(cs_attr['identifier'])
        #print(server_util['current_state'])    
        print(_('Server ID:{}\tName:{}\tManage Command: {} --sadd {}').format(cs_attr["identifier"],cs_attr["name"],appfile,cs_attr["identifier"]))

if(args.sadd):
    if not basecon.check() == True:
        basecon = rpConnection(config.yamlconfig['instance'], rpConfig.getsecure('bearer'))
    print(_('{} - Add Server({}):').format(appfile,args.sadd))
    e = basecon.server_exists(args.sadd)    
    if e == True:
        server = rpServer(args.sadd)
        print(_('Fetching status data from {}...').format(basecon.get_instance_url()))
        server.fetch(basecon)
        if 'serverlist' in config.yamlconfig and config.yamlconfig['serverlist'] is not None:
            #if server in config.yamlconfig['serverlist']:
            for configuredserver in config.yamlconfig['serverlist']:
                if server.identifier == configuredserver.identifier:
                    parser.error(_("Error storing server {} in configuration, server already configured.").format(server.name))
        print(_("Adding \"{}\" with ID {} to configuration.").format(server.name, server.identifier))
        try:
            config.yamlconfig['serverlist'].append(server)
        except KeyError:            
            config.yamlconfig['serverlist'] = [server]
        except AttributeError:
            config.yamlconfig['serverlist'] = [server]
        except Exception as err:
            parser.error(_("Error storing server {} in configuration.\nDetail: {}").format(server.name, err))
        print(_('Writing configuration to {}...').format(str(configfile)), end='')
        config.write_config(configfile)
        print(_("...done"))
        
    else:
        parser.error(_("Specified server does not exist.\nDetail: {}").format(e))

if(args.sremove):
    if not basecon.check() == True:
        basecon = rpConnection(config.yamlconfig['instance'], rpConfig.getsecure('bearer'))
    print(_('{} - Remove Server({}):').format(appfile,args.sremove))
    e = basecon.server_exists(args.sremove)    
    if e == True:
        if len(config.yamlconfig['serverlist']) > 0:
            for server in config.yamlconfig['serverlist']:
                if server.identifier == args.sremove:
                    config.yamlconfig['serverlist'].remove(server)
                    print(_('Server {} Removed').format(server.name))
                    print(_('Writing configuration to {}...').format(str(configfile)), end='')
                    config.write_config(configfile)
                    print(_("...done"))
                else:
                    print(_('Server {} Skipped').format(server.name))
        else:
            print(_('No Servers Registered.'))
    else:
        if(args.force):
                if 'serverlist' in config.yamlconfig:
                    for server in config.yamlconfig['serverlist']:
                        if server.identifier == args.remove:
                            config.yamlconfig['serverlist'].remove(server)
                            print(_('Server {} Removed Forcibly.').format(args.force))
        else:
            parser.error(_("Specified server does not exist in pterodactyl, use --force to force removal\nDetail: {}").format(e))

if(args.slist):
    if not basecon.check() == True:
        basecon = rpConnection(config.yamlconfig['instance'], rpConfig.getsecure('bearer'))
    print(_('{} - Managed Servers:').format(appfile))
    print(_('Fetching status data from {}...').format(basecon.get_instance_url()))
    if len(config.yamlconfig['serverlist']) > 0:
        for server in config.yamlconfig['serverlist']:
            server.fetch(basecon)
        for server in config.yamlconfig['serverlist']:       
            print(_("Server ID:{}\tName:{}\tState:{}\tUUID:{}").format(server.identifier, server.name, server.state, server.uuid))
    else:
        print(_('No managed servers configured. Use --list-available and --sadd to add rust servers to manage.'))
    
if(args.smanage):
    if not basecon.check() == True:
        basecon = rpConnection(config.yamlconfig['instance'], rpConfig.getsecure('bearer'))
    print(_('{} - Manage Server({}):').format(appfile,args.smanage))
    e = basecon.server_exists(args.smanage)
    if e == True:        
        if(not args.umod and not args.gen and not args.update and not args.remove and not args.ftpauth):
            print(_("Option {} requires one of {}").format('--smanage','--umod/--gen/--update/--remove'))
        else:
            if(args.umod):
                print(_('Confirming server {} details... ').format(args.smanage))
                if config.server_ismanaged(args.smanage):                     
                    server = config.server_getmanaged(args.smanage)
                    server.fetch(basecon)
                    if server.state == 'running':
                        print(_("Downloading Umod Plugin {}...").format(args.umod))
                        dlresp = rpUtil.https_download_file(umodbase + args.umod, cachedir) 
                        if dlresp:
                            filepath = os.path.join(cachedir,args.umod)                            
                            if rpUtil.file_isnt_zero(filepath):                                                                
                                    print(_("Uploading Umod Plugin {}...").format(args.umod))                                    
                                    ox = config.yamlconfig['remoteoxideplugins']                                    
                                    if(ox):
                                        remotepath = "{}/{}".format(ox,args.umod)
                                        if not server.pluginexists(basecon,remotepath):
                                            server.uploadplugin(basecon, filepath, remotepath, False)
                                        else:
                                            details,resp = server.file_detail(basecon,remotepath)
                                            deleteresp = input(_("File {} already exists at destination with size {} and modify data {}, delete(y/n)?".format(args.umod, details['size'], details['modified_at'])))
                                            if deleteresp in ["Y","y","Yes","yes"]:
                                                ok, err = server.uploadplugin(basecon, filepath, remotepath, True)
                                                if not ok:
                                                    for e in err:
                                                        print(e)


                                        #region - moved to rpServer.uploadplugin  
                                        # uploadresp = server.file_upload(basecon,filepath)
                                        # if not uploadresp.ok:
                                        #     logger.error(_("File upload failed with {}".format(uploadresp.text)))
                                        # else:
                                        #     renameresp = server.file_rename(basecon, args.umod, "{}/{}".format(ox,args.umod))                                            
                                        #     if(not renameresp.ok):                                                                                        
                                        #         if renameresp.json():
                                        #             errdetail = renameresp.json()['errors'][0]['detail']                                            
                                        #             if "Cannot move or rename file, destination already exists" in errdetail:
                                        #                 details = server.file_detail(basecon, "{}/{}".format(ox,args.umod))
                                        #                 if 'size' in details and 'modified_at' in details:
                                        #                     deleteresp = input(_("File {} already exists at destination with size {} and modify data {}, delete(y/n)?".format(args.umod, details['size'], details['modified_at'])))
                                        #                     if deleteresp in ["y","Y","Yes","YES"]:
                                        #                         server.file_delete(basecon,  "{}/{}".format(ox,args.umod))
                                        #                         renameresp = server.file_rename(basecon, args.umod, "{}/{}".format(ox,args.umod))                                            
                                        #                         if(not renameresp.ok):
                                        #                             logger.error(_("We deleted {} however the move still failing with {}, Detail: {}.".format(args.umod,renameresp.text, errdetail)))
                                        #                         else:
                                        #                             rpUtil.pluginreload(basecon,server, logger, args.umod)
                                        #             else:
                                        #                 logger.error(_("File move failed with {}, Detail: {}.".format(renameresp.text, errdetail)))
                                        #     else:
                                        #         rpUtil.pluginreload(basecon,server, logger, args.umod)
                                        #endregion
                            else:
                                print(_("File download appeared successful however the resulting file is empty, Check {}".format(filepath)))
                        else:
                            print(_("Downloading {} from {} failed, {}".format(args.umod, umodbase, d.strerror)))    

                    else:
                        print(_("Server {} is not running. The server must be running for this operation.").format(args.smanage)) 
                else:
                    print(_("Server {} is not managed by {}").format(args.smanage,appfile))
            if(args.gen):
                print(_('gen'))
            if(args.update):
                print(_('update'))
            if(args.remove):
                print (_('remove'))
            if(args.ftpauth):
                p = getpass.getpass(prompt=_("SFTP Password:"))
                server = config.server_getmanaged(args.smanage)
                server.fetch(basecon)
                server.sftp_set_auth(args.ftpauth)                
                if server.sftp_check_auth(appname,basecon,p):              
                    rpConfig.setsecure("ftp_"+args.ftpauth,p)
                    print(_('Successfully Authenticated {}').format(args.ftpauth))
                    print(_('Writing configuration to {}...').format(str(configfile)), end='')
                    config.write_config(configfile)
                    print(_("...done"))
                else:
                    print(_('Failure Authenticating {}').format(args.ftpauth))

                
    else:
        parser.error(_("Specified server does not exist in pterodactyl.\nDetail: {}").format(e))     


#parser.print_help()
#if(args.update):
#print(yaml.dump(config.yamlconfig))
