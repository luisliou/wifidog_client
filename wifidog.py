import sys
import time
import json
import subprocess
import urlparse
import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
ServerClass  = BaseHTTPServer.HTTPServer
Protocol     = "HTTP/1.0"
whitelist    = ['backgrd.jpg', 'functions.js', 'login.html', 'style.css', 'swat.png', 'trylater.html']
MAX_FAIL = 3
class LoginUser():
  def __init__(self, mac, ip):
      self.mac = mac
      self.ip = ip
      self.failtimes = 0
      self.firstfailtime = 0
      self.islogedin = False
  def getmac(self):
      return self.mac
  def getip(self):
      return self.ip
  def getfailtimes(self):
      return self.failtimes
  def addfail(self, lasttime):
      if self.failtimes > MAX_FAIL:
         self.failtimes = 0
         self.firstfailtime = 0
      self.failtimes = self.failtimes + 1
      if self.firstfailtime == 0:
         self.firstfailtime = lasttime
      print "addfail:" + self.mac
      print "ip:" + self.ip + " times:" + str(self.failtimes)
  def getfirstfailtime(self):
      return self.firstfailtime
  def setLogedin(self):
      self.islogedin = True
      self.failtimes = 0
      self.firstfailtime = 0
  def isLogedin(self):
      return self.islogedin

class UserAdmin():
  def __init__(self):
      self.list = []
  def userValidate(self, mac, ip):
      global MAX_FAIL
      for user in self.list:
        if user.getmac() == mac and user.getip() == ip:
           print "FailTimes:" + str(user.getfailtimes())
           print "Time:" + str(time.time() - user.getfirstfailtime())
           if user.getfailtimes() > MAX_FAIL and time.time() - user.getfirstfailtime() < 60 :
              return False #too many retries 
      return True   #user is normal
  def addFailUser(self, mac, ip):
      for user in self.list:
          if user.getmac() == mac and user.getip() == ip:
             user.addfail(time.time())
             return
      newUser = LoginUser(mac, ip)
      newUser.addfail(time.time())
      self.list.append(newUser)
  def addLogedUser(self, mac, ip):
      for user in self.list:
          if user.getmac() == mac and user.getip() == ip:
             user.setLogedin()
             return
  def isLogedin(self, mac, ip):
      for user in self.list:
          if user.getmac() == mac and user.getip() == ip:
             return user.isLogedin()

users = UserAdmin()

class MyHandler(SimpleHTTPRequestHandler):
  def do_GET(self):
    global users
    print self.path
    if self.path.startswith('/ping'):
      print(self.headers)
      self.send_response(200)
      self.end_headers()
      self.wfile.write('Pong')
      self.wfile.close()
    else:
      if self.path.startswith('/login'):
        f = open("login.html", "r")
        self.wfile.write(f.read())
        f.close()
        self.wfile.close()
      else:
        if self.path.startswith('/auth'):
          parsed = urlparse.urlparse(self.path)
          urldata = urlparse.parse_qs(parsed.query)
          mac = urldata['mac'][0]
          ip  = urldata['ip'][0]
          print(users.userValidate(mac,ip))
          if users.userValidate(mac, ip) == False:
             print "Too many tries!"
             #f = open("trylater.html", "r")
             #self.wfile.write(f.read())
             #f.close()
             #self.wfile.close()
             self.wfile.write('Auth: 0')
             self.wfile.close()
             return
          if urldata['stage'][0] == 'login':
            p = subprocess.Popen(['curl', '-s', '-k', '-X', 'GET', '-H', "x-ha-access:4567890", '-H', "Content-Type: application/json", "https://192.168.0.210:8123/api/states/sensor.guest_wifi_password"], stdout=subprocess.PIPE, stderr = subprocess.PIPE, shell=False)
            stdout, errout = p.communicate()
            token = json.loads(stdout)['state']
            print "Right token:" + token
            print urlparse.parse_qs(parsed.query)['token'][0]
            self.send_response(200)
            self.end_headers()
            if token != urlparse.parse_qs(parsed.query)['token'][0] and users.isLogedin(mac, ip) == False:
              self.wfile.write('Auth: 0')
              print "Fail!"
              self.wfile.close()
              users.addFailUser(urldata['mac'][0], urldata['ip'][0])
              return
            else:
              self.wfile.write('Auth: 1')
              print "Succ!"
              self.wfile.close()
              users.addLogedUser(urldata['mac'][0], urldata['ip'][0])
          else:
              if urldata['stage'][0] == 'counter':
                 if users.isLogedin(urldata['mac'][0], urldata['ip'][0]):
                    self.wfile.write('Auth: 1')
                    print "Succ!"
                    self.wfile.close()
                 else:
                    self.wfile.write('Auth: 0')
                    print "Fail to login!"
                    self.wfile.close()
        else:
          if self.path.startswith('/portal/'):
            f = open("succ.html", "r")
            self.wfile.write(f.read())
            f.close()
            self.wfile.close()
          else:
              if self.path.startswith('/gw_message.php'):
                 f = open("trylater.html", "r")
                 self.wfile.write(f.read())
                 f.close()
                 self.wfile.close()
              else:
                 if(self.path.replace('/', '') in whitelist):
                   SimpleHTTPRequestHandler.do_GET(self)
                 else:
                   print "error"
 
if sys.argv[1:]:
    port = int(sys.argv[1])
else:
    port = 80
server_address = ('0.0.0.0', port)
 
MyHandler.protocol_version = Protocol
httpd = ServerClass(server_address, MyHandler)
 
sa = httpd.socket.getsockname()
print "Serving HTTP on", sa[0], "port", sa[1], "..."
httpd.serve_forever()
