# -- coding: utf-8 --
import hou
import os
import re
import time
import json
from weslie import wes_Utils as wesutil
from hutil.Qt import QtWidgets, QtUiTools



uipath = hou.expandString("$WESLIB")+"/python_panels/ui/Wes_ProjBrowser.ui"

#Cutomize Config
projects_root = "S:/Project/"
concept_folder = ["01_Concept/01_Storyboard","01_Concept/02_Layout","01_Concept/03_Anim","01_Concept/04_Ref"]
projects_folder_preset = [concept_folder,"02_Assets","03_HProject","04_Comp","05_Cut","06_Submit","07_Feedback"]
hproject_name = "03_HProject"
tests_root = "S:/Test/"

#Project Config
test_names = os.listdir(tests_root)


class ProjBrowser(QtWidgets.QWidget):
    def __init__(self):
        super(ProjBrowser,self).__init__()

        #Get Env
        self.jobenv = hou.getenv("JOB")+"/"

        #Load UI File
        uiloader = QtUiTools.QUiLoader()
        self.ui = uiloader.load(uipath)

        #Find Widgets
        self.current_shot = self.ui.findChild(QtWidgets.QPushButton, "current_shot")
        self.enter_shot = self.ui.findChild(QtWidgets.QPushButton, "enter_shot")
        self.new_shot = self.ui.findChild(QtWidgets.QPushButton, "new_shot")
        self.set_proj_hip = self.ui.findChild(QtWidgets.QPushButton, "set_proj_hip")
        self.load_hip = self.ui.findChild(QtWidgets.QPushButton, "load_hip")
        self.open_folder = self.ui.findChild(QtWidgets.QPushButton, "open_folder")
        self.save_big_ver = self.ui.findChild(QtWidgets.QPushButton, "save_big_ver")
        self.save_small_ver = self.ui.findChild(QtWidgets.QPushButton, "save_small_ver")
        self.hiplist = self.ui.findChild(QtWidgets.QListWidget, "hiplist")
        self.project_path = self.ui.findChild(QtWidgets.QLabel,"project_path")
        self.scene_label = self.ui.findChild(QtWidgets.QLabel,"scene_label")
        self.scene = self.ui.findChild(QtWidgets.QComboBox,"scene")
        self.shot_label = self.ui.findChild(QtWidgets.QLabel,"shot_label")
        self.shot = self.ui.findChild(QtWidgets.QComboBox,"shot")
        self.person = self.ui.findChild(QtWidgets.QLineEdit,"person")
        self.content = self.ui.findChild(QtWidgets.QLineEdit,"content")
        self.proj_name = self.ui.findChild(QtWidgets.QComboBox,"proj_name")
        self.browse_mode = self.ui.findChild(QtWidgets.QComboBox,"browse_mode")
        self.new_proj = self.ui.findChild(QtWidgets.QPushButton, "new_proj")
        


        #Initialize Some Widgets
        self.havescene = False
        self.haveshot = False
        self.refresh_by_jobenv()
        self.refreshprojnames()
        self.refreshprojconfig()
        self.refreshscenelist()
        self.refreshshotlist()


        #Connect Buttons
        self.browse_mode.currentTextChanged.connect(self.refreshprojnames)
        self.proj_name.currentTextChanged.connect(self.refreshprojconfig)
        self.new_proj.clicked.connect(self.newproj)
        self.scene.currentTextChanged.connect(self.refreshshotlist)
        self.enter_shot.clicked.connect(self.entershot)
        self.new_shot.clicked.connect(self.newshot)
        self.current_shot.clicked.connect(self.currentshot)
        self.set_proj_hip.clicked.connect(self.setprojhip)
        self.save_small_ver.clicked.connect(self.savesmallversion)
        self.save_big_ver.clicked.connect(self.savebigversion)
        self.hiplist.doubleClicked.connect(self.loadhip)
        self.load_hip.clicked.connect(self.loadhip)
        self.open_folder.clicked.connect(self.openfolder)


        #Set Layout        
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.ui)  
        self.setLayout(layout)
        


    def getshotinfo(self):
        self.jobenv = hou.getenv("JOB")+"/"
        try:
            scene = re.findall(r"SCENE_\d*", self.jobenv)[-1]
            shot = re.findall(r"SHOT_\d*", self.jobenv)[-1]
        except Exception as IndexError:
            scene = ""
            shot = ""
        scene = scene.replace("SCENE_","")
        shot = shot.replace("SHOT_","")
        self.scene.setCurrentText(scene)
        self.shot.setCurrentText(shot)

    def gethipver(self):
        hipname = hou.hipFile.basename()
        digits = re.findall(r"\d+", hipname)
        self.sver = digits[-1]
        self.bver = digits[-2]

    def refreshprojnames(self):
        self.proj_name.clear()
        if(self.browse_mode.currentText()=="Project"):
            proj_names = os.listdir(projects_root)
            proj_names.reverse()
            self.proj_name.addItems(proj_names)
            self.scene.setEnabled(True)
            self.scene_label.setEnabled(True)
            self.shot.setEnabled(True)
            self.shot_label.setEnabled(True)
            self.new_shot.setEnabled(True)
        elif(self.browse_mode.currentText()=="Test"):
            proj_names = os.listdir(tests_root)
            proj_names.reverse()
            self.proj_name.addItems(proj_names)
            self.scene.setEnabled(False)
            self.scene_label.setEnabled(False)
            self.shot.setEnabled(False)
            self.shot_label.setEnabled(False)
            self.new_shot.setEnabled(False)

    def refresh_by_jobenv(self):
        #print("Fuck")
        self.jobenv = hou.getenv("JOB")+"/"
        self.refresh_hiplist(self.jobenv)

    def refresh_hiplist(self, proj_dir):
        self.hiplist.clear()
        self.project_path.setText(proj_dir)
        files = os.listdir(proj_dir)
        files.reverse()
        for file in files:
            if file.endswith(".hip"):
                self.hiplist.addItem(file)

    def refreshprojconfig(self):
        if(self.browse_mode.currentText()=="Project"):
            self.loadconfig()
            self.refreshscenelist()
            self.refreshshotlist()

    def loadconfig(self):
        projname = self.proj_name.currentText()
        jsonpath = projects_root + projname + "/" + "project_config.json"

        #initial config data
        self.proj_config = {}
        self.date = ""
        self.projpurename = ""
        self.res = [1920,1080]
        self.fps = 25
        self.havescene = True
        self.haveshot = True

        #load config data
        if os.path.exists(jsonpath):
            with open(jsonpath) as json_file:
                self.proj_config = json.load(json_file)
            self.date = self.proj_config.get("date")
            self.projpurename = self.proj_config.get("projname")
            self.res = self.proj_config.get("res")
            self.fps = self.proj_config.get("fps")
            self.havescene = self.proj_config.get("havescene")
            self.haveshot = self.proj_config.get("haveshot")
        else:
            hou.ui.displayMessage(u"Cannot find Project Config File | 找不到项目配置文件")

        #Set Scene and Shot State
        if self.havescene:
            self.scene_label.setEnabled(True)
            self.scene.setEnabled(True)
        else:
            self.scene_label.setEnabled(False)
            self.scene.setEnabled(False)
        if self.haveshot:
            self.shot_label.setEnabled(True)
            self.shot.setEnabled(True)
        else:
            self.shot_label.setEnabled(False)
            self.shot.setEnabled(False)

    def refreshscenelist(self):
        self.scene.clear()
        projname = self.proj_name.currentText()
        if self.havescene:
            proj_root = projects_root + projname +'/'+ hproject_name + "/"
            scene_list = []
            if os.path.exists(proj_root):
                scenes = os.listdir(proj_root)
                for scene in scenes:
                    scene = scene.replace("SCENE_","")
                    scene_list.append(scene)
            self.scene.addItems(scene_list)
    
    def refreshshotlist(self):
        self.shot.clear()
        projname = self.proj_name.currentText()
        if self.haveshot:
            shot_list = []
            proj_root = ""
            if self.havescene:
                scene = self.scene.currentText()
                proj_root = projects_root + projname+'/'+ hproject_name + "/SCENE_" + scene + "/"
            else:
                proj_root = projects_root + projname+'/'+ hproject_name + "/"
            if os.path.exists(proj_root):
                shots = os.listdir(proj_root)
                for shot in shots:
                    shot = shot.replace("SHOT_","")
                    shot_list.append(shot)
            self.shot.addItems(shot_list)


    def newproj(self):
        new_projname = ""
        if(self.browse_mode.currentText()=="Project"):
            new_projname = self.confignewproj()
            if not new_projname == "" or new_projname.isspace():
                self.refreshprojnames()
                self.proj_name.setCurrentText(new_projname)
        elif(self.browse_mode.currentText()=="Test"):
            new_projname = self.confignewtest()
            if not new_projname == "" or new_projname.isspace():
                self.refreshprojnames()
                self.proj_name.setCurrentText(new_projname)
        
    def newshot(self):
        proj_pure_name = self.projpurename
        proj_name = self.proj_name.currentText()
        proj_root = projects_root + proj_name +'/'+ hproject_name + "/"
        proj_fps = self.fps
        scene = self.scene.currentText()
        shot = self.shot.currentText()
        content = self.content.text()
        #proj_dir = proj_root+ "SCENE_"+scene + "/SHOT_"+ shot + "/"
        #hipname = proj_pure_name + "_sc"+scene+"_shot"+shot+"_"+content+"_v01.001"+".hip"
        proj_dir = proj_root
        hipname = proj_pure_name
        if self.havescene:
            proj_dir += "SCENE_" +scene + "/"
            hipname += "_sc"+scene
        if self.haveshot:
            proj_dir += "SHOT_" +shot +"/"
            hipname += "_shot"+shot
        hipname += "_"+content+"_v01.001"+".hip"

        if os.path.exists(proj_dir):
            hou.ui.displayMessage(u"Shot Already Exists | 该镜头已存在噢")
        else:
            create_mode = hou.ui.displayCustomConfirmation(u"新建hip还是直接另存当前hip?",buttons=("新建","另存"))
            if create_mode !=1:
                os.makedirs(proj_dir)
                hou.hipFile.clear()
                hou.hipFile.save(proj_dir+hipname)
                hou.setFps(proj_fps)
                os.environ["JOB"] = proj_dir
                hou.allowEnvironmentToOverwriteVariable("JOB",True)
                self.refresh_by_jobenv()
            else:
                os.makedirs(proj_dir)
                hou.hipFile.save(proj_dir+hipname)
                hou.setFps(proj_fps)
                os.environ["JOB"] = proj_dir
                hou.allowEnvironmentToOverwriteVariable("JOB",True)
                self.refresh_by_jobenv()
        self.refreshscenelist()
        self.refreshshotlist()

    def setprojhip(self):
        hipenv = hou.getenv("HIP")
        os.environ["JOB"] = hipenv
        hou.allowEnvironmentToOverwriteVariable("JOB",True)

    def entershot(self):
        proj_name = self.proj_name.currentText()
        proj_root = ""
        if(self.browse_mode.currentText()=="Project"):
            proj_root = projects_root + proj_name +'/'+ hproject_name + "/"
        elif(self.browse_mode.currentText()=="Test"):
            proj_root = tests_root + proj_name +'/'
        scene = self.scene.currentText()
        shot = self.shot.currentText()
        #proj_dir = proj_root+ "SCENE_"+scene + "/_SHOT_"+ shot + "/"
        proj_dir = proj_root
        if self.havescene:
            proj_dir += "SCENE_" +scene + "/"
        if self.haveshot:
            proj_dir += "SHOT_" +shot +"/"
        if os.path.exists(proj_dir):
            self.refresh_hiplist(proj_dir)
        else:
            hou.ui.displayMessage(u"The Shot does not exist, please create a new shot | 该镜头不存在,请先新建镜头")

    def currentshot(self):
        self.getshotinfo()
        self.refresh_by_jobenv()

        
    def savesmallversion(self):
        self.gethipver()
        hipname = hou.hipFile.name()
        hiphead = "_".join(hipname.split("_")[0:-1])
        self.sver = str("%03d"%(int(self.sver)+1))
        hiptail = "_"+ "v"+ self.bver+ "."+ self.sver+ ".hip"
        hipname = hiphead + hiptail
        if not os.path.exists(hipname):
            hou.hipFile.save(hipname)
        else:
            hou.ui.displayMessage(u"Hip FIle Already Exists | 文件已存在(日后会优化该选项)")
        self.refresh_by_jobenv()

    def savebigversion(self):
        self.gethipver()
        hipname = hou.hipFile.name()
        hiphead = "_".join(hipname.split("_")[0:-1])
        self.sver = "001"
        self.bver = str("%02d"%(int(self.bver)+1))
        hiptail = "_"+ "v"+ self.bver+ "."+ self.sver+ ".hip"
        hipname = hiphead + hiptail
        if not os.path.exists(hipname):
            hou.hipFile.save(hipname)
            self.refresh_by_jobenv()
        else:
            hou.ui.displayMessage(u"Hip FIle Already Exists | 文件已存在(日后会优化该选项)")

    def loadhip(self):
        hippath = self.project_path.text() + self.hiplist.selectedItems()[0].data(0)
        hou.hipFile.load(hippath)

    def openfolder(self):
        os.startfile(self.project_path.text())

    def makeprojdir(self, proj_root, projects_folder_preset):
        for folder in projects_folder_preset:
            if isinstance(folder, str):
                dir = "/".join([proj_root, folder])
                os.makedirs(dir)
            elif isinstance(folder, list):
                self.makeprojdir(proj_root,folder)

    def confignewproj(self):
        #Initial Message Box
        msgbox = QtWidgets.QMessageBox(hou.qt.mainWindow())
        msgbox.setWindowTitle('Config Project')
        msgbox.setText("Config the Project")
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)

        #Set InputInfo
        now = time.localtime()
        date_label = QtWidgets.QLabel("Date")
        date_year = QtWidgets.QComboBox()
        years = ["2021","2022","2023","2024"]
        date_year.addItems(years)
        date_year.setCurrentText(str(now[0]))
        date_mon = QtWidgets.QComboBox()
        mons = []
        mon = 1
        while mon<=12:
            mons.append(str(mon))
            mon+=1
        date_mon.addItems(mons)
        date_mon.setCurrentText(str(now[1]))

        projname_label = QtWidgets.QLabel("Project Name")
        projname = QtWidgets.QLineEdit()

        res_label = QtWidgets.QLabel("Res")
        resx = QtWidgets.QLineEdit("1920")
        resy = QtWidgets.QLineEdit("1080")

        fps_label = QtWidgets.QLabel("FPS")
        fps = QtWidgets.QLineEdit("25")
        havescene = QtWidgets.QCheckBox("Scene")
        havescene.setChecked(True)
        haveshot = QtWidgets.QCheckBox("Shot")
        haveshot.setChecked(True)

        #Set SubLayout
        date_layout = QtWidgets.QHBoxLayout()
        date_layout.addWidget(date_label)
        date_layout.addWidget(date_year)
        date_layout.addWidget(date_mon)

        projname_layout = QtWidgets.QHBoxLayout()
        projname_layout.addWidget(projname_label)
        projname_layout.addWidget(projname)

        fps_layout = QtWidgets.QHBoxLayout()
        fps_layout.addWidget(fps_label)
        fps_layout.addWidget(fps)

        res_layout = QtWidgets.QHBoxLayout()
        res_layout.addWidget(res_label)
        res_layout.addWidget(resx)
        res_layout.addWidget(resy)

        #Set Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(date_layout)
        layout.addLayout(projname_layout)
        layout.addLayout(res_layout)
        layout.addLayout(fps_layout)
        layout.addWidget(havescene)
        layout.addWidget(haveshot)
        msgbox.layout().addLayout(layout,1,0,1,16)

        #Show Windows
        new_projname = ""
        choice = msgbox.exec_()
        

        #Get Info
        if choice == QtWidgets.QMessageBox.Ok:
            date_year = date_year.currentText()
            date_mon = str("%02d"%int(date_mon.currentText()))
            projname = projname.text()
            resx = int(resx.text())
            resy = int(resy.text())
            fps = int(fps.text())
            havescene = havescene.isChecked()
            haveshot = haveshot.isChecked()
            proj_root = projects_root + date_year + date_mon + "_" + projname +"/"
            

            empty = False
            if projname == "" or projname.isspace():
                hou.ui.displayMessage(u"Empty Project Name | 空白项目名",severity=hou.severityType.Error)
            elif os.path.exists(proj_root):
                hou.ui.displayMessage(u"Project Already Exists | 项目已存在",severity=hou.severityType.Error)
            else:
                self.makeprojdir(proj_root,projects_folder_preset)
                proj_info = {
                    "date":date_year+date_mon,
                    "projname":projname,
                    "res":[resx,resy],
                    "fps":fps,
                    "havescene":havescene,
                    "haveshot":haveshot
                    }
                print("------------------------------")
                print("Create Project Path: "+ proj_root)
                print(proj_info)
                print("------------------------------")
                proj_info_json = json.dumps(proj_info)
                jsonfile = "/".join([proj_root, "project_config.json"])
                with open(jsonfile,"w") as config_file:
                    config_file.write(proj_info_json)
            new_projname = date_year + date_mon + "_" + projname
        return new_projname

    def confignewtest(self):
        #Initial Message Box
        msgbox = QtWidgets.QMessageBox(hou.qt.mainWindow())
        msgbox.setWindowTitle('Config Project')
        msgbox.setText("Config the Project")
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)

        #Set InputInfo
        now = time.localtime()
        date_label = QtWidgets.QLabel("Date")
        date_year = QtWidgets.QComboBox()
        years = ["2021","2022","2023","2024"]
        date_year.addItems(years)
        date_year.setCurrentText(str(now[0]))
        date_mon = QtWidgets.QComboBox()
        mons = []
        mon = 1
        while mon<=12:
            mons.append(str(mon))
            mon+=1
        date_mon.addItems(mons)
        date_mon.setCurrentText(str(now[1]))
        date_day = QtWidgets.QComboBox()
        days = []
        day = 1
        while day<=31:
            days.append(str(day))
            day+=1
        date_day.addItems(days)
        date_day.setCurrentText(str(now[2]))

        projname_label = QtWidgets.QLabel("Test Name")
        projname = QtWidgets.QLineEdit()

        #Set SubLayout
        date_layout = QtWidgets.QHBoxLayout()
        date_layout.addWidget(date_label)
        date_layout.addWidget(date_year)
        date_layout.addWidget(date_mon)
        date_layout.addWidget(date_day)

        projname_layout = QtWidgets.QHBoxLayout()
        projname_layout.addWidget(projname_label)
        projname_layout.addWidget(projname)

        #Set Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(date_layout)
        layout.addLayout(projname_layout)
        msgbox.layout().addLayout(layout,1,0,1,16)

        #Show Windows
        new_projname = ""
        choice = msgbox.exec_()

        #Get Info
        if choice == QtWidgets.QMessageBox.Ok:
            date_year = date_year.currentText()
            date_mon = str("%02d"%int(date_mon.currentText()))
            date_day = str("%02d"%int(date_day.currentText()))
            projname = projname.text()
            test_root = tests_root + date_year + date_mon + date_day + "_" + projname +"/"
            
            empty = False
            if projname == "" or projname.isspace():
                hou.ui.displayMessage(u"Empty Test Name | 空白项目名",severity=hou.severityType.Error)
            elif os.path.exists(test_root):
                hou.ui.displayMessage(u"Test Already Exists | 项目已存在",severity=hou.severityType.Error)
            else:
                os.makedirs(test_root)
                print("------------------------------")
                print("Create Test Path: "+ test_root)
                print("------------------------------")

            new_projname = date_year + date_mon + date_day + "_" + projname
        return new_projname