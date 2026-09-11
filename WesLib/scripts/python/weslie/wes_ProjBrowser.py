# -- coding: utf-8 --
import hou
import os
import re
import time
import json
from hutil.Qt import QtWidgets, QtUiTools, QtCore, QtGui


def _norm_path(path):
    return os.path.normpath(hou.text.expandString(path)).replace("\\", "/")


def _join_path(*parts):
    return os.path.normpath(os.path.join(*parts)).replace("\\", "/")


def _hou_env_path(name):
    value = hou.getenv(name)
    if not value:
        return ""
    return _norm_path(value) + "/"


def _year_items():
    current_year = time.localtime()[0]
    return [str(year) for year in range(current_year - 2, current_year + 3)]


module_dir = os.path.dirname(os.path.abspath(__file__))
mypath = _join_path(module_dir, os.pardir, os.pardir, os.pardir)

#Project Structure
concept_folder = ["01_Concept/01_Storyboard","01_Concept/02_Layout","01_Concept/03_Anim","01_Concept/04_Ref"]
projects_folder_preset = [concept_folder,"02_Assets","03_HProject","04_Comp","05_Cut","06_Submit","07_Feedback"]
hproject_name = "03_HProject"

#Set UI Path
uipath = _join_path(mypath, "python_panels", "ui", "Wes_ProjBrowser_ch.ui")
_MAX_QT_SIZE = 16777215


def _text_width(font_metrics, text):
    if hasattr(font_metrics, "horizontalAdvance"):
        return font_metrics.horizontalAdvance(text)
    return font_metrics.width(text)


def _dpi_scale():
    scales = [1.0]
    if hasattr(hou.ui, "scaledSize"):
        try:
            scaled = float(hou.ui.scaledSize(100))
            if scaled > 0:
                scales.append(scaled / 100.0)
        except Exception:
            pass

    app = QtWidgets.QApplication.instance()
    screen = app.primaryScreen() if app and hasattr(app, "primaryScreen") else None
    if screen:
        scales.append(screen.logicalDotsPerInch() / 96.0)
        scales.append(screen.devicePixelRatio())
    return max(1.0, min(max(scales), 2.5))


def _scaled_size(value, scale=None):
    scale = _dpi_scale() if scale is None else scale
    return int(round(value * scale))


def _scale_stylesheet_lengths(widget, scale):
    stylesheet = widget.styleSheet()
    if not stylesheet:
        return

    def repl(match):
        return match.group(1) + str(_scaled_size(int(match.group(2)), scale)) + match.group(3)

    stylesheet = re.sub(r"(border-radius:\s*)(\d+)(px)", repl, stylesheet)
    stylesheet = re.sub(r"(padding(?:-[a-z]+)?:\s*)(\d+)(px)", repl, stylesheet)
    widget.setStyleSheet(stylesheet)


class ProjBrowser(QtWidgets.QWidget):
    def __init__(self):
        super(ProjBrowser,self).__init__()

        #Initialize
        self.config_root()
        self.jobenv = _hou_env_path("JOB")

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
        config_icon.addPixmap(QtGui.QPixmap(_join_path(mypath, "python_panels", "ui", "setting_96.png")))
        self.root_config.setIcon(config_icon)
        self.root_config.setIconSize(QtCore.QSize(18,18))
        self._apply_dpi_aware_sizes()

        #Set Layout   
        self.content.setAlignment(QtCore.Qt.AlignLeft)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.ui)  
        self.setLayout(layout)
        


    def _set_scaled_minimum_height(self, widget, base_height, scale, extra_padding=10):
        metrics = QtGui.QFontMetrics(widget.font())
        height = max(widget.minimumHeight(), _scaled_size(base_height, scale), metrics.height() + _scaled_size(extra_padding, scale))
        widget.setMinimumHeight(height)
        if widget.maximumHeight() < _MAX_QT_SIZE:
            widget.setMaximumHeight(_MAX_QT_SIZE)
        return height

    def _set_scaled_minimum_width(self, widget, width):
        widget.setMinimumWidth(width)
        if widget.maximumWidth() < width:
            widget.setMaximumWidth(_MAX_QT_SIZE)

    def _combo_content_width(self, combo, scale):
        metrics = QtGui.QFontMetrics(combo.font())
        texts = [combo.itemText(index) for index in range(combo.count())]
        if combo.currentText():
            texts.append(combo.currentText())
        text_width = max([_text_width(metrics, text) for text in texts] or [0])
        return text_width + _scaled_size(44, scale)

    def _apply_dpi_aware_sizes(self):
        scale = _dpi_scale()

        for layout in self.ui.findChildren(QtWidgets.QLayout):
            spacing = layout.spacing()
            if spacing > 0:
                layout.setSpacing(_scaled_size(spacing, scale))
            margins = layout.contentsMargins()
            layout.setContentsMargins(
                _scaled_size(margins.left(), scale),
                _scaled_size(margins.top(), scale),
                _scaled_size(margins.right(), scale),
                _scaled_size(margins.bottom(), scale),
            )

        for button in self.ui.findChildren(QtWidgets.QPushButton):
            if button is self.root_config:
                continue
            metrics = QtGui.QFontMetrics(button.font())
            self._set_scaled_minimum_height(button, 25, scale, 10)
            min_width = max(button.minimumWidth(), _text_width(metrics, button.text()) + _scaled_size(36, scale))
            self._set_scaled_minimum_width(button, min_width)
            button.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
            _scale_stylesheet_lengths(button, scale)

        for label in self.ui.findChildren(QtWidgets.QLabel):
            if label.maximumWidth() >= _MAX_QT_SIZE:
                continue
            metrics = QtGui.QFontMetrics(label.font())
            min_width = _text_width(metrics, label.text()) + _scaled_size(10, scale)
            self._set_scaled_minimum_width(label, min_width)
            label.setSizePolicy(QtWidgets.QSizePolicy.Fixed, label.sizePolicy().verticalPolicy())

        for combo in self.ui.findChildren(QtWidgets.QComboBox):
            self._set_scaled_minimum_height(combo, 26, scale, 8)
            min_width = max(combo.minimumWidth(), self._combo_content_width(combo, scale))
            if combo is self.browse_mode:
                min_width = 150
                combo.setMinimumWidth(min_width)
                combo.setMaximumWidth(min_width)
                combo.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            else:
                if combo in (self.scene, self.shot):
                    min_width = max(min_width, 150)
                combo.setMinimumWidth(min_width)
                combo.setMaximumWidth(_MAX_QT_SIZE)
                combo.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)

        for line_edit in self.ui.findChildren(QtWidgets.QLineEdit):
            self._set_scaled_minimum_height(line_edit, 26, scale, 8)
            line_edit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        icon_button_size = _scaled_size(24, scale)
        icon_size = _scaled_size(18, scale)
        self.root_config.setMinimumSize(icon_button_size, icon_button_size)
        self.root_config.setMaximumSize(icon_button_size, icon_button_size)
        self.root_config.setIconSize(QtCore.QSize(icon_size, icon_size))
        self.root_config.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        _scale_stylesheet_lengths(self.root_config, scale)
    def getshotinfo(self):
        self.jobenv = _hou_env_path("JOB")
        try:
            scene = re.findall(r"SCENE_\d*", self.jobenv)[-1]
            shot = re.findall(r"SHOT_\d*", self.jobenv)[-1]
        except IndexError:
            scene = ""
            shot = ""
        scene = scene.replace("SCENE_","")
        shot = shot.replace("SHOT_","")
        self.scene.setCurrentText(scene)
        self.shot.setCurrentText(shot)

    def gethipver(self):
        hipname = hou.hipFile.basename()
        digits = re.findall(r"\d+", hipname)
        if len(digits) < 2:
            hou.ui.displayMessage(u"Cannot find version number in current hip name | 当前 hip 文件名中没有找到版本号")
            return False
        self.sver = digits[-1]
        self.bver = digits[-2]
        return True

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
        self.jobenv = _hou_env_path("JOB")
        self.hipenv = _hou_env_path("HIP")
        if os.path.exists(self.jobenv):
            self.refresh_hiplist(self.jobenv)
        elif os.path.exists(self.hipenv):
            print(u'$JOB path does not exist, using $HIP instead')
            self.refresh_hiplist(self.hipenv)
        else:
            self.hiplist.clear()
            self.project_path.setText("")

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
        jsonpath = _join_path(self.projects_root, projname, "project_config.json")
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
            proj_root = _join_path(self.projects_root, projname, hproject_name) + "/"
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
                proj_root = _join_path(self.projects_root, projname, hproject_name, "SCENE_" + scene) + "/"
            else:
                proj_root = _join_path(self.projects_root, projname, hproject_name) + "/"
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
            proj_root = _join_path(self.projects_root, proj_name, hproject_name) + "/"
        elif self.browse_mode.currentText() == "Test":
            self.havescene = False
            self.haveshot = False
            proj_name = self.proj_name.currentText()
            try:
                proj_pure_name = "_".join(proj_name.split("_")[1:])
            except IndexError:
                proj_pure_name = proj_name
            if not proj_pure_name:
                proj_pure_name = proj_name
            proj_root = _join_path(self.tests_root, proj_name) + "/"
        else:
            return
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
            if os.path.exists(_join_path(proj_dir, hipname)):
                path_exist = True
                hou.ui.displayMessage(u"Shot Already Exists | 该镜头已存在噢")
        if not path_exist:
            create_mode = hou.ui.displayCustomConfirmation(u"Create New empty hip or Save current hip as new hip? | 新建空白hip还是直接另存当前hip?",buttons=(u"Create | 新建",u"Save as | 另存",u"Cancel | 取消"))
            if create_mode ==0:
                if scene_or_shot:
                    if not os.path.exists(proj_dir):
                        os.makedirs(proj_dir)
                hou.hipFile.clear()
                hou.hipFile.save(_join_path(proj_dir, hipname))
                hou.setFps(proj_fps)
                os.environ["JOB"] = proj_dir
                hou.allowEnvironmentToOverwriteVariable("JOB",True)
                self.refresh_by_jobenv()
            elif create_mode ==1:
                if scene_or_shot:
                    if not os.path.exists(proj_dir):
                        os.makedirs(proj_dir)
                hou.hipFile.save(_join_path(proj_dir, hipname))
                hou.setFps(proj_fps)
                os.environ["JOB"] = proj_dir
                hou.allowEnvironmentToOverwriteVariable("JOB",True)
                self.refresh_by_jobenv()
        self.refreshscenelist()
        self.refreshshotlist()

    def setprojhip(self):
        hipenv = hou.getenv("HIP")
        if not hipenv:
            return
        os.environ["JOB"] = hipenv
        hou.allowEnvironmentToOverwriteVariable("JOB",True)

    def entershot(self):
        proj_name = self.proj_name.currentText()
        scene = self.scene.currentText()
        shot = self.shot.currentText()
        proj_root = ""
        proj_dir = ""
        if(self.browse_mode.currentText()=="Project"):
            proj_root = _join_path(self.projects_root, proj_name, hproject_name) + "/"
            proj_dir = proj_root
            if self.havescene:
                proj_dir += "SCENE_" +scene + "/"
            if self.haveshot:
                proj_dir += "SHOT_" +shot +"/"
        elif(self.browse_mode.currentText()=="Test"):
            proj_root = _join_path(self.tests_root, proj_name) + "/"
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
        if not self.gethipver():
            return
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
        if not self.gethipver():
            return
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
        selected_items = self.hiplist.selectedItems()
        if not selected_items:
            return
        hippath = _join_path(self.project_path.text(), selected_items[0].data(0))
        hou.hipFile.load(hippath)

    def openfolder(self):
        folder = self.project_path.text()
        if not folder or not os.path.exists(folder):
            return
        if hasattr(hou.ui, "showInFileBrowser"):
            hou.ui.showInFileBrowser(folder)
        elif hasattr(os, "startfile"):
            os.startfile(folder)

    def makeprojdir(self, proj_root, projects_folder_preset):
        for folder in projects_folder_preset:
            if isinstance(folder, str):
                directory = _join_path(proj_root, folder)
                if not os.path.exists(directory):
                    os.makedirs(directory)
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
        date_year.addItems(_year_items())
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
            if not resx.text().isdigit() or not resy.text().isdigit() or not fps.text().isdigit():
                hou.ui.displayMessage(u"Wrong Input Type | 输入的信息格式错误",severity=hou.severityType.Error)
                return ""
            resx = int(resx.text())
            resy = int(resy.text())
            fps = int(fps.text())
            havescene = havescene.isChecked()
            haveshot = haveshot.isChecked()
            new_projname = date_year + date_mon + "_" + projname
            proj_root = _join_path(self.projects_root, new_projname) + "/"

            if projname == "" or projname.isspace():
                hou.ui.displayMessage(u"Empty Project Name | 空白项目名",severity=hou.severityType.Error)
                return ""
            elif os.path.exists(proj_root):
                hou.ui.displayMessage(u"Project Already Exists | 项目已存在",severity=hou.severityType.Error)
                return ""
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
                jsonfile = _join_path(proj_root, "project_config.json")
                with open(jsonfile,"w") as config_file:
                    config_file.write(proj_info_json)
                return new_projname
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
        date_year.addItems(_year_items())
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
            new_projname = date_year + date_mon + date_day + "_" + projname
            test_root = _join_path(self.tests_root, new_projname) + "/"
            
            if projname == "" or projname.isspace():
                hou.ui.displayMessage(u"Empty Test Name | 空白项目名",severity=hou.severityType.Error)
                return ""
            elif os.path.exists(test_root):
                hou.ui.displayMessage(u"Test Already Exists | 项目已存在",severity=hou.severityType.Error)
                return ""
            else:
                os.makedirs(test_root)
                print("------------------------------")
                print("Create Test Path: "+ test_root)
                print("------------------------------")
                return new_projname
        return new_projname

    def config_root(self):
        initial_config_info = {}
        self.projects_root = ""
        self.tests_root = ""
        self.default_res = [1920,1080]
        self.default_fps = 25
        # Check and Load Config
        jsonfile = _join_path(mypath, "python_panels", "project_browser_config.json")
        if os.path.exists(jsonfile):
            with open(jsonfile) as json_file:
                initial_config_info = json.load(json_file)
            # print (initial_config_info)
            self.projects_root = initial_config_info.get("projects_root") or ""
            self.tests_root = initial_config_info.get("tests_root") or ""
            self.default_res = initial_config_info.get("default_res") or self.default_res
            self.default_fps = initial_config_info.get("default_fps") or self.default_fps
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
                projects_root = _norm_path(projects_root)
                tests_root = _norm_path(tests_root)
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
                config_dir = _join_path(mypath, "python_panels")
                jsonfile = _join_path(config_dir, "project_browser_config.json")
                with open(jsonfile,"w") as config_file:
                    config_file.write(initial_info_json)
            self.config_root()
            self.refreshprojnames()
