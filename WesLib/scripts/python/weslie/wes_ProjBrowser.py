# -- coding: utf-8 --
import hou
import os
import re
import time
import json
from hutil.Qt import QtWidgets, QtUiTools, QtCore, QtGui

mypath = __file__[:-19]
mypath = mypath[:-22]

#Project Structure
concept_folder = ["01_Concept/01_Storyboard","01_Concept/02_Layout","01_Concept/03_Anim","01_Concept/04_Ref"]
projects_folder_preset = [concept_folder,"02_Assets","03_HProject","04_Comp","05_Cut","06_Submit","07_Feedback"]
hproject_name = "03_HProject"

#Set UI Path
uipath = mypath+"/python_panels/ui/Wes_ProjBrowser_ch.ui"


class ProjBrowser(QtWidgets.QWidget):
    def __init__(self):
        super(ProjBrowser,self).__init__()

        #Initialize
        self.config_root()
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
        self.root_config = self.ui.findChild(QtWidgets.QPushButton, "root_config")
        


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
        self.new_proj.clicked.connect(self.newproj)
        self.proj_name.currentTextChanged.connect(self.refreshprojconfig)
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
        self.root_config.clicked.connect(self.config_root_setting)

        #Set Icon
        config_icon = QtGui.QIcon()
        config_icon.addPixmap(QtGui.QPixmap(mypath+"/python_panels/ui/setting_96.png"))
        self.root_config.setIcon(config_icon)
        self.root_config.setIconSize(QtCore.QSize(18,18))

        #Set Layout   
        self.content.setAlignment(QtCore.Qt.AlignLeft)
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
        #Project Mode
        if(self.browse_mode.currentText()=="Project"):
            self.scene.setEnabled(True)
            self.scene_label.setEnabled(True)
            self.shot.setEnabled(True)
            self.shot_label.setEnabled(True)
            self.new_shot.setEnabled(True)
            self.enter_shot.setEnabled(True)
            self.new_proj.setEnabled(True)
            if os.path.exists(self.projects_root):
                proj_names = os.listdir(self.projects_root)
                proj_names.reverse()
            else:
                proj_names = [u"项目根目录不存在，请点击左侧小齿轮配置"]
                self.scene.setEnabled(False)
                self.scene_label.setEnabled(False)
                self.shot.setEnabled(False)
                self.shot_label.setEnabled(False)
                self.new_shot.setEnabled(False)
                self.enter_shot.setEnabled(False)
                self.new_proj.setEnabled(False)
            self.proj_name.addItems(proj_names)
        #Test Mode
        elif(self.browse_mode.currentText()=="Test"):
            self.scene.setEnabled(False)
            self.scene_label.setEnabled(False)
            self.shot.setEnabled(False)
            self.shot_label.setEnabled(False)
            self.new_shot.setEnabled(True)
            self.enter_shot.setEnabled(True)
            self.new_proj.setEnabled(True)
            if os.path.exists(self.tests_root):
                proj_names = os.listdir(self.tests_root)
                proj_names.reverse()
            else:
                proj_names = [u"测试根目录不存在，请点击左侧小齿轮配置"]
                self.scene.setEnabled(False)
                self.scene_label.setEnabled(False)
                self.shot.setEnabled(False)
                self.shot_label.setEnabled(False)
                self.new_shot.setEnabled(False)
                self.enter_shot.setEnabled(False)
                self.new_proj.setEnabled(False)
            self.proj_name.addItems(proj_names)
        #Custom Mode
        else:
            self.scene.setEnabled(False)
            self.scene_label.setEnabled(False)
            self.shot.setEnabled(False)
            self.shot_label.setEnabled(False)
            self.new_shot.setEnabled(False)
            self.enter_shot.setEnabled(False)
            self.new_proj.setEnabled(False)
    def refresh_by_jobenv(self):
        #print("Fuck")
        self.jobenv = hou.getenv("JOB")+"/"
        self.hipenv = hou.getenv("HIP")+"/"
        if os.path.exists(self.jobenv):
            self.refresh_hiplist(self.jobenv)
        else:
            print(u'$JOB path does not exist, using $HIP instead')
            self.refresh_hiplist(self.hipenv)

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
        jsonpath = self.projects_root + projname + "/" + "project_config.json"
        #initial config data
        self.proj_config = {}
        self.date = ""
        self.projpurename = ""
        self.res = self.default_res
        self.fps = self.default_fps
        self.havescene = False
        self.haveshot = False

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
        elif projname != "" and not projname.isspace():
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
            proj_root = self.projects_root + projname +'/'+ hproject_name + "/"
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
                proj_root = self.projects_root + projname+'/'+ hproject_name + "/SCENE_" + scene + "/"
            else:
                proj_root = self.projects_root + projname+'/'+ hproject_name + "/"
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
            if new_projname != "" and new_projname.isspace()==False:
                self.refreshprojnames()
                self.proj_name.setCurrentText(new_projname)
        elif(self.browse_mode.currentText()=="Test"):
            new_projname = self.confignewtest()
            if new_projname != "" and new_projname.isspace()==False:
                self.refreshprojnames()
                self.proj_name.setCurrentText(new_projname)
        
    def newshot(self):
        if self.browse_mode.currentText() == "Project":
            proj_pure_name = self.projpurename
            proj_name = self.proj_name.currentText()
            proj_root = self.projects_root + proj_name +'/'+ hproject_name + "/"
        if self.browse_mode.currentText() == "Test":
            self.havescene = False
            self.haveshot = False
            proj_name = self.proj_name.currentText()
            try:
                proj_pure_name = "_".join(proj_name.split("_")[1:])
            except:
                proj_pure_name = proj_name
            proj_root = self.tests_root + proj_name + "/"
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
        scene_or_shot = False
        path_exist = False
        if self.havescene or self.haveshot:
            scene_or_shot = True
            if os.path.exists(proj_dir):
                path_exist = True
                hou.ui.displayMessage(u"Shot Already Exists | 该镜头已存在噢")
        elif not self.havescene or not self.haveshot:
            scene_or_shot = False
            if os.path.exists(proj_dir+hipname):
                path_exist = True
                hou.ui.displayMessage(u"Shot Already Exists | 该镜头已存在噢")
        if not path_exist:
            create_mode = hou.ui.displayCustomConfirmation(u"Create New empty hip or Save current hip as new hip? | 新建空白hip还是直接另存当前hip?",buttons=(u"Create | 新建",u"Save as | 另存",u"Cancel | 取消"))
            if create_mode ==0:
                if scene_or_shot:
                    os.makedirs(proj_dir)
                hou.hipFile.clear()
                hou.hipFile.save(proj_dir+hipname)
                hou.setFps(proj_fps)
                os.environ["JOB"] = proj_dir
                hou.allowEnvironmentToOverwriteVariable("JOB",True)
                self.refresh_by_jobenv()
            elif create_mode ==1:
                if scene_or_shot:
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
        scene = self.scene.currentText()
        shot = self.shot.currentText()
        proj_root = ""
        proj_dir = ""
        if(self.browse_mode.currentText()=="Project"):
            proj_root = self.projects_root + proj_name +'/'+ hproject_name + "/"
            proj_dir = proj_root
            if self.havescene:
                proj_dir += "SCENE_" +scene + "/"
            if self.haveshot:
                proj_dir += "SHOT_" +shot +"/"
        elif(self.browse_mode.currentText()=="Test"):
            proj_root = self.tests_root + proj_name +'/'
            proj_dir = proj_root
        #proj_dir = proj_root+ "SCENE_"+scene + "/_SHOT_"+ shot + "/"
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
        msgbox = QtWidgets.QMessageBox()
        msgbox.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
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
        projname.setStyleSheet("border-style: none;")

        res_label = QtWidgets.QLabel("Res")
        resx = QtWidgets.QLineEdit("1920")
        resy = QtWidgets.QLineEdit("1080")
        resx.setStyleSheet("border-style: none;")
        resy.setStyleSheet("border-style: none;")

        fps_label = QtWidgets.QLabel("FPS")
        fps = QtWidgets.QLineEdit("25")
        fps.setStyleSheet("border-style: none;")
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
            proj_root = self.projects_root + date_year + date_mon + "_" + projname +"/"
            

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
        msgbox = QtWidgets.QMessageBox()
        msgbox.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
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
            test_root = self.tests_root + date_year + date_mon + date_day + "_" + projname +"/"
            
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

    def config_root(self):
        initial_config_info = {}
        self.projects_root = ""
        self.tests_root = ""
        self.default_res = [1920,1080]
        self.default_fps = 25
        # Check and Load Config
        jsonfile = mypath + "/python_panels" + "/project_browser_config.json"
        if os.path.exists(jsonfile):
            with open(jsonfile) as json_file:
                initial_config_info = json.load(json_file)
            print (initial_config_info)
            self.projects_root = initial_config_info.get("projects_root")
            self.tests_root = initial_config_info.get("tests_root")
            self.default_res = initial_config_info.get("default_res")
            self.default_fps = initial_config_info.get("default_fps")
        else:
            hou.ui.displayConfirmation(u"未找到初始化配置文件，请点击小齿轮图标进行初始化配置")
        return initial_config_info

    def config_root_setting(self):
        # Pop up Config Window
        input_confirm, input_info = hou.ui.readMultiInput(u"Initialize Your Browser | 初始化配置", ('Projects Root','Tests Root','Default_ResX','Default_ResY','Default_FPS'),
            initial_contents = ("","","1920","1080","25"),
            title = "Input Config",
            buttons=("OK", "Cancel"),
            default_choice=0, 
            close_choice=1,
            )
        #print(input_confirm)
        #print(input_info)
        if input_confirm == 0:
            check = False
            projects_root =  input_info[0]
            tests_root = input_info[1]
            default_resx = input_info[2]
            default_resy = input_info[3]
            default_fps = input_info[4]
            # Check if Every Info is OK
            type_is_ok = True
            check_digit_list = input_info[2:5]
            for info in check_digit_list:
                if info == "" or info.isspace() or not info.isdigit():
                    hou.ui.displayMessage(u"Wrong Input Type | 输入的信息格式错误",severity=hou.severityType.Error)
                    type_is_ok = False
                    break
            if type_is_ok:
                if not os.path.exists(projects_root) or os.path.isfile(projects_root):
                    hou.ui.displayMessage(u"Projects Root does not exists | 项目根目录路劲不存在",severity=hou.severityType.Error)
                elif not os.path.exists(tests_root) or os.path.isfile(tests_root):
                    hou.ui.displayMessage(u"Tests Root does not exists | 测试根目录路劲不存在",severity=hou.severityType.Error)
                else:
                    check = True
            
            # Create Config File
            if check:
                projects_root = projects_root.replace("\\","/")
                tests_root = tests_root.replace("\\","/")
                if projects_root[-1] != "/":
                    projects_root += "/"
                if tests_root[-1] != "/":
                    tests_root += "/"
                initial_info = {
                    "projects_root" : projects_root,
                    "tests_root" : tests_root,
                    "default_res" : [int(default_resx),int(default_resy)],
                    "default_fps" : int(default_fps)
                }
                initial_info_json = json.dumps(initial_info)
                config_dir = mypath + "/python_panels"
                jsonfile = "/".join([config_dir, "project_browser_config.json"])
                with open(jsonfile,"w") as config_file:
                    config_file.write(initial_info_json)
            self.config_root()
            self.refreshprojnames()