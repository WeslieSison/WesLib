# -*- coding: utf-8 -*-
import hou
import os
import shutil

def setcamres(node, resx, resy):
    kids = node.allNodes()
    for kid in kids:
        if kid.type().name() == "cam":
            kid.setParms({"resx": resx, "resy": resy})


def updateabcarchive(node, resx=1920, resy=1080):
    if node.type().name() == "alembicarchive":
        node.parm("buildHierarchy").pressButton()
        node.parm("reloadGeometry").pressButton()
        setcamres(node, resx, resy)


def updatepackage_fordeveloper():
    houdini_ver = hou.applicationVersionString()[:-4]
    
    package_path = hou.expandString("$HOME")+"/Houdini"+houdini_ver+"/packages/WesLib"
    target_path = "S:/GitHub/Repository/WesLib/WesLib"

    confirm = True
    if os.path.exists(package_path):
        if os.path.exists(target_path):
            confirm = hou.ui.displayConfirmation("确认是否要更新WesLib")
            if confirm:
                shutil.rmtree(target_path)
                print("--- 预删除 ---")
        if confirm:
            print("--- 正在更新WesLib ---")
            shutil.copytree(package_path,target_path)
            print("--- 更新完成 ---")
    else:
        hou.ui.displayMessage("Package路径不存在")


def updatepackage_foruser():
    houdini_ver = hou.applicationVersionString()[:-4]
    
    target_path = hou.expandString("$HOME")+"/Houdini"+houdini_ver+"/packages/WesLib"
    package_path = "S:/GitHub/Repository/WesLib/WesLib"

    confirm = True
    if os.path.exists(package_path):
        if os.path.exists(target_path):
            confirm = hou.ui.displayConfirmation("确认是否要更新WesLib")
            if confirm:
                shutil.rmtree(target_path)
                print("--- 预删除 ---")
        if confirm:
            print("--- 正在更新WesLib ---")
            shutil.copytree(package_path,target_path)
            hou.ui.displayMessage("更新完成, 重启Houdini后生效")
    else:
        hou.ui.displayMessage("Package路径不存在")