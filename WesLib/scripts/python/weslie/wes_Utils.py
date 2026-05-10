# -*- coding: utf-8 -*-
import hou
import os
import shutil


def _norm_path(path):
    return os.path.normpath(hou.text.expandString(path))


def _module_package_root():
    module_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(module_dir, os.pardir, os.pardir, os.pardir))


def _package_root():
    weslib = hou.getenv("WESLIB")
    if weslib:
        return _norm_path(weslib)
    return _module_package_root()


def _source_package_root():
    source_root = hou.getenv("WESLIB_SOURCE_ROOT") or hou.getenv("WESLIB_DEV_ROOT")
    if source_root:
        return _norm_path(source_root)
    return _module_package_root()


def _replace_tree_with_backup(src, dst):
    src = os.path.abspath(src)
    dst = os.path.abspath(dst)
    if src == dst:
        raise shutil.Error("Source and target are the same path: {0}".format(src))

    backup = dst + ".bak"
    if os.path.exists(backup):
        shutil.rmtree(backup)
    if os.path.exists(dst):
        shutil.move(dst, backup)
    try:
        shutil.copytree(src, dst)
    except Exception:
        if os.path.exists(dst):
            shutil.rmtree(dst)
        if os.path.exists(backup):
            shutil.move(backup, dst)
        raise


def copy_tree(src, dst, symlinks=False):
    names = os.listdir(src)
    if not os.path.isdir(dst):
        os.makedirs(dst)

    for name in names:
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        if symlinks and os.path.islink(srcname):
            linkto = os.readlink(srcname)
            os.symlink(linkto, dstname)
        elif os.path.isdir(srcname):
            copy_tree(srcname, dstname, symlinks)
        else:
            if os.path.isdir(dstname):
                os.rmdir(dstname)
            elif os.path.isfile(dstname):
                os.remove(dstname)
            shutil.copy2(srcname, dstname)

def hou_copy_tree(src, dst, symlinks=False):
    names = os.listdir(src)
    if not os.path.isdir(dst):
        os.makedirs(dst)
    i = 0    
    errors = []
    with hou.InterruptableOperation("正在拷贝文件","Copying",True) as operation:
        for name in names:
            num_tasks = len(names)
            percent = float(i) / float(num_tasks)
            operation.updateLongProgress(percent,name)
            srcname = os.path.join(src, name)
            dstname = os.path.join(dst, name)
            try:
                if os.path.isdir(srcname):
                    hou_copy_tree(srcname, dstname, symlinks)
                else:
                    if os.path.isdir(dstname):
                        os.rmdir(dstname)
                    elif os.path.isfile(dstname):
                        os.remove(dstname)
                    shutil.copy2(srcname, dstname)
            except (IOError, os.error) as why:
                errors.append((srcname, dstname, str(why)))
            except OSError as err:
                errors.extend(err.args[0])
            i += 1
        try:
            shutil.copystat(src, dst)
        except OSError:
            pass
        if errors:
            #raise shutil.Error(errors)
            hou.ui.displayMessage("\n".join([str(error) for error in errors]))
            operation.updateProgress(0)



def updatepackage_fordeveloper():
    choosefiles = hou.ui.displayCustomConfirmation("choose files or dirs?",buttons=("dirs","files"))
    if choosefiles:
        selected_files = hou.ui.selectFile( 
        start_directory = "$WESLIB/",
        title = "Choose Files" , 
        file_type = hou.fileType.Any, 
        multiple_select = True, )
    else :
        selected_files = hou.ui.selectFile( 
        start_directory = "$WESLIB/",
        title = "Choose Dirs" , 
        file_type = hou.fileType.Directory, 
        multiple_select = True, 
        )

    if not selected_files:
        return

    files = [path for path in selected_files.split(" ; ") if path]

    package_dir = _package_root()
    target_dir = _source_package_root()
    if os.path.abspath(package_dir) == os.path.abspath(target_dir):
        hou.ui.displayMessage("Set WESLIB_SOURCE_ROOT or WESLIB_DEV_ROOT before updating developer files.")
        return

    confirm = True
    if os.path.exists(package_dir):
        if os.path.exists(target_dir):
            confirm = hou.ui.displayConfirmation(u"确认是否要更新WesLib")
        if confirm:
            print("--- Updating WesLib ---")
            for afile in files:
                absfile = hou.text.expandString(afile)
                relpath = os.path.relpath(absfile, package_dir)
                target_path = os.path.join(target_dir, relpath)
                if os.path.isdir(absfile):
                    hou_copy_tree(absfile, target_path)
                elif os.path.isfile(absfile):
                    target_parent = os.path.dirname(target_path)
                    if not os.path.exists(target_parent):
                        os.makedirs(target_parent)
                    shutil.copy2(absfile,target_path)
            print("--- Update Finished ---")
    else:
        hou.ui.displayMessage(u"Package路径不存在")


def updatepackage_foruser():
    target_path = _norm_path("$HOUDINI_USER_PREF_DIR/packages/WesLib")
    package_path = _source_package_root()

    confirm = True
    if os.path.exists(package_path):
        if os.path.exists(target_path):
            confirm = hou.ui.displayConfirmation("确认是否要更新WesLib")
        if confirm:
            print("--- 正在更新WesLib ---")
            try:
                _replace_tree_with_backup(package_path,target_path)
            except shutil.Error as err:
                hou.ui.displayMessage(str(err))
                return
            hou.ui.displayMessage("更新完成, 重启Houdini后生效")
    else:
        hou.ui.displayMessage("Package路径不存在")



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

def fetchcam(node):
    objnet = hou.node("/obj")
    node_pos = node.position()

    cams = [kid for kid in node.allNodes() if kid.type().name() == "cam"]
    for kid in cams:
        copycams = objnet.copyItems([kid], channel_reference_originals=True)
        for copycam in copycams:
            copy_pos = node_pos
            copy_pos += hou.Vector2(3,0)
            copycam.setPosition(copy_pos)
                
            #Clean Shits
            copycam.parmTuple("win").deleteAllKeyframes()
            copycam.parmTuple("winsize").deleteAllKeyframes()
            copycam.parm("aspect").deleteAllKeyframes()
            copycam.parm("shutter").deleteAllKeyframes()
            copycam.parm("fstop").deleteAllKeyframes()
            copycam.parm("near").deleteAllKeyframes()
            copycam.parm("far").deleteAllKeyframes()
            copycam.setParms({"near":0.001, "far":10000})

            fetch = copycam.createInputNode(0,"fetch")
            fetch.setParms({"fetchobjpath":kid.path() ,"useinputoffetched":1})
            fetch.setDisplayFlag(False)

def abcloader():
    #Create Nodes for each abc files
    abc_files = hou.ui.selectFile( 
        title = "Select Alembic" , 
        file_type = hou.fileType.Geometry, 
        multiple_select = True, 
        pattern = "*.abc"
    )
    if not abc_files:
        return

    abc_list = [abc_file for abc_file in abc_files.split(" ; ") if abc_file]
    geo_nodes = []
    for abc_path in abc_list:
        abc_name = os.path.splitext(abc_path)[0]
        abc_name = abc_name.split("/")[-1]

        geo = hou.node("/obj").createNode("geo", abc_name)
        geo_nodes.append(geo)
        alembic = geo.createNode("alembic", "Import_"+abc_name)
        alembic.parm("fileName").set(abc_path)

        unpack = alembic.createOutputNode("unpack")
        unpack.setParms({"transfer_attributes":"*", "transfer_groups":"*"})
        unpack.createOutputNode("convert").createOutputNode("null","OUT_Unpack")

        out = alembic.createOutputNode("null","OUT_Pack")
        out.setRenderFlag(True)
        out.setDisplayFlag(True)
        
        geo.layoutChildren()


    #configure Global Scale
    sels = hou.selectedNodes()
    if len(sels) != 0 and sels[-1].type().category().label() == "Objects" and sels[-1].type().name() == "null":
        scale = sels[-1]
    else:
        scale = hou.node("/obj").createNode("null","Global_Scale")
        scale.setParms({"scale":0.1})
        scale.setDisplayFlag(False)

    #connect geo_node to null
    for geo_node in geo_nodes:
        geo_node.setInput(0,scale)

    #layout nodes
    geo_nodes.append(scale)
    hou.node("/obj").layoutChildren(geo_nodes)

def abcloaderfolder():
    abc_dirs = hou.ui.selectFile( 
        start_directory = "$HIP/",
        title = "选择ABC文件夹" , 
        file_type = hou.fileType.Directory, 
        multiple_select = True, 
    )
    if not abc_dirs:
        return

    dirs = [abc_dir for abc_dir in abc_dirs.split(" ; ") if abc_dir]
    if not dirs:
        return
    abc_kind_files_all = []
    abc_kinds = []

    #Get Root Path
    dir_root = dirs[0].split("/")
    del dir_root[-1]
    del dir_root[-1]
    dir_root = "/".join(dir_root)
    dir_root_abs = hou.expandString(dir_root)
    #Get Data
    for abc_dir in dirs:
        abc_dir_abs = hou.expandString(abc_dir)

        abc_kind = abc_dir.split("/")[-2]
        abc_kinds.append(abc_kind)

        abc_files =[]
        for walk_home, walk_dirs, walk_files in os.walk(abc_dir_abs):
            for filename in walk_files:
                filepath = walk_home+"/"+filename
                filepath = filepath.replace(dir_root_abs+"/"+abc_kind,"")
                abc_files.append(filepath)
            
        abc_kind_files = []
        for abc_file in abc_files:
            abc_kind_file = abc_kind+abc_file
            abc_kind_files.append(abc_kind_file)
            abc_kind_files_all.append(abc_kind_file)

    abc_kind_files_sel = hou.ui.selectFromTree(abc_kind_files_all, title = "选择需要的abc文件")

    #Create GEO Nodes for each folder and create&merge alembic node for each sub-Object
    geo_nodes = []
    n = 0
    for abc_dir in dirs:
        abc_kind = abc_kinds[n]
        geo = hou.node("/obj").createNode("geo", abc_kind)
        geo_nodes.append(geo)

        alembic_nodes = []
        for abc_kind_file_sel in abc_kind_files_sel:
            if abc_kind_file_sel.find(abc_kind) != -1:

                abc_name = abc_kind_file_sel.split("/")[-1]
                abc_name = abc_name.split(".")
                del abc_name[-1]
                abc_name = ".".join(abc_name)

                alembic = geo.createNode("alembic", abc_name)
                alembic.parm("fileName").set(dir_root +"/"+ abc_kind_file_sel)
                group = alembic.createOutputNode("groupcreate","group_"+abc_name)
                group.setParms({"groupname":abc_name})
                alembic_nodes.append(group)

        merge = geo.createNode("merge")
        for node in alembic_nodes:
            merge.setNextInput(node)
        
        unpack = merge.createOutputNode("unpack")
        unpack.setParms({"transfer_attributes":"*", "transfer_groups":"*"})
        unpack.createOutputNode("convert").createOutputNode("null","OUT_Unpack")
        out = merge.createOutputNode("null","OUT_Pack")
        out.setRenderFlag(True)
        out.setDisplayFlag(True)
        geo.layoutChildren()
        n+=1

    #configure Global Scale
    sels = hou.selectedNodes()
    if len(sels) != 0 and sels[-1].type().category().label() == "Objects" and sels[-1].type().name() == "null":
        scale = sels[-1]
    else:
        scale = hou.node("/obj").createNode("null","Global_Scale")
        scale.setParms({"scale":0.1})
        scale.setDisplayFlag(False)

    #connect geo_node to null
    for geo_node in geo_nodes:
        geo_node.setInput(0,scale)

    #layout nodes
    geo_nodes.append(scale)
    hou.node("/obj").layoutChildren(geo_nodes)

