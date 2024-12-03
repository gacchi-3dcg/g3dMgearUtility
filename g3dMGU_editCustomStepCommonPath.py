### ------------------------------------------------------   

# ライブラリ

### ------------------------------------------------------

# system
import os
import shutil

# maya
import maya.cmds as cmds

### ------------------------------------------------------ 

# 概要

### ------------------------------------------------------ 

"""スクリプト

    このスクリプトは、mGearのカスタムステップにて共通するファイルパスを
    編集・更新するためのツールです。

    機能概要

        01. ガイドノードの検出 (findGuideNode)
            特定の属性 (preCustomStep) を持つノードを検索します。
            見つからない場合はエラーを発生させます。

        02. 共通ディレクトリパスの抽出 (extractCommonPath)
            指定された文字列から複数のファイルパスを解析し、それらの共通部分を抽出します。

        03. パス編集用ダイアログの作成 (showPathEditorDialog)
            現在のパスを表示し、新しいパスを入力・選択するためのGUIを提供します。
            新しいパスをユーザーが指定することで、その結果をコールバック関数に渡します。

        04. ファイルの存在確認 (checkFileExistence)
            指定されたベースディレクトリとファイルリストに基づき、
            存在するファイルと存在しないファイルを分類します。

        05. カスタムステップ文字列の更新 (updateCustomStepStrings)
            ノードの属性 (preCustomStep と postCustomStep) に含まれるファイルパスを、
            新しい共通パスに置き換えます。
            ファイルが存在しない場合は、ユーザーに「継続」または「中断」の選択肢を提供します。

        06. エントリーポイント (main)
            スクリプト全体の処理をまとめています。以下を行います：
                ガイドノードの取得
                現在のパスの共通部分を抽出
                パス編集ダイアログの表示
                新しいパスを指定された場合の更新処理

    処理の流れ

        01. main関数が実行され、ガイドノードを探す。
        02. ガイドノードの属性値 (preCustomStep および postCustomStep) から
            現在の共通パスを抽出。
        03. GUIダイアログでユーザーが新しいパスを指定。
        04. ファイルの存在確認を行い、必要に応じて更新処理を実施。

    History:
        2024/12/02  ver1.0.0:  スクリプト作成 [ Maya2024 / mGear version: 4.2.2 ]
"""
VERSION = "1.1.0"
"""
    特徴
        ・ファイルの存在確認とエラー対応
            存在しないファイルがある場合、変更の継続または中断をユーザーが選べる。

        ・ユーザーインターフェース
            Mayaのダイアログを使用して直感的な操作を提供。

        ・拡張性
        カスタムステップの管理やパス編集の際の確認プロセスを追加可能。
"""
### ------------------------------------------------------

def findGuideNode(defaultGuide="guide"):
    """
    ガイドノードを見つける。見つからない場合、推定して返します。

    Args:
        defaultGuide (str): デフォルトのガイドノード名

    Returns:
        str: 見つかったガイドノード名
    """
    if cmds.objExists(f"{defaultGuide}.preCustomStep"):
        return defaultGuide

    for trns in cmds.ls(type="transform"):
        if cmds.objExists(f"{trns}.preCustomStep"):
            return trns

    raise RuntimeError("No valid guide node with attribute 'preCustomStep' found.")


def extractCommonPath(inputString):
    """
    指定された文字列から各パスをリスト化し、共通するディレクトリパスを抽出します。

    Args:
        inputString (str): 対象の文字列

    Returns:
        str: 共通するパス文字列
    """
    try:
        paths = [item.split(" | ")[1] for item in inputString.split(",")]
        commonPath = os.path.commonpath(paths).replace("\\", "/")
        return commonPath
    except Exception as e:
        cmds.warning(f"Failed to extract common path: {e}")
        return ""


def incrementVersion(path):
    """
    パス内のバージョン番号 (_vXX) をインクリメントした新しいパスを生成します。

    Args:
        path (str): 元のパス。

    Returns:
        str: インクリメントされた新しいパス。
    """
    import re
    match = re.search(r"(.*)(_v\d+)$", path)
    if match:
        base = match.group(1)
        version = match.group(2)
        newVersion = int(version[2:]) + 1
        return f"{base}_v{newVersion:02d}"
    return path  # バージョン番号がない場合はそのまま返す


def duplicateFolder(srcFolder):
    """
    指定フォルダを複製して、新しいバージョンのフォルダを作成します。

    Args:
        srcFolder (str): 元のフォルダのパス。

    Returns:
        str: 新しいフォルダのパス。
    """
    if not os.path.exists(srcFolder):
        cmds.error(f"Source folder does not exist: {srcFolder}")
        return None

    newFolder = incrementVersion(srcFolder)
    try:
        shutil.copytree(srcFolder, newFolder)
        cmds.confirmDialog(
            title="Success",
            message=f"Folder duplicated successfully:\n{newFolder}",
            button=["OK"],
            defaultButton="OK",
            icon="information"
        )
        return newFolder
    except Exception as e:
        cmds.error(f"Failed to duplicate folder: {e}")
        return None


def showPathEditorDialog(currentPath, onConfirm):
    """
    GUIで現在のパスを表示し、新しいパスを入力するダイアログを作成します。

    Args:
        currentPath (str): 現在のパス
        onConfirm (function): 新しいパスが指定された際に実行する関数
    """
    def onOK(*args):
        newPath = cmds.textField("pathInputField", q=True, text=True)
        cmds.deleteUI(window)
        onConfirm(newPath)

    def onAddVer(*args):
        newPath = duplicateFolder(currentPath)
        cmds.deleteUI(window)
        onConfirm(newPath)

    def onBrowse(*args):
        folderPath = cmds.fileDialog2(dialogStyle=2, fileMode=3, okCaption="Select Folder")
        if folderPath:
            cmds.textField("pathInputField", e=True, text=folderPath[0])

    def onCancel(*args):
        cmds.deleteUI(window)

    windowName = "mgear_customstep_editPathDialog"

    if cmds.window(windowName, exists=True):
        cmds.deleteUI(windowName)

    window = cmds.window(
        windowName, 
        title=f"mgear Customstep EditPath {VERSION}", 
        widthHeight=(500, 100)
        )
    cmds.columnLayout(adjustableColumn=True)

    # rowLayout を開始
    cmds.rowLayout(nc=3, adj=2, cal=(2, "left"))  
    cmds.text(label="Current Path: ")
    cmds.text(label=currentPath)
    cmds.text(label="              ")
    cmds.setParent('..')  # rowLayout を終了

    cmds.separator(h=8, style="none")

    # rowLayout を開始
    cmds.rowLayout(nc=3, adj=2)  
    cmds.text(label="New Path    :")
    cmds.textField("pathInputField", text=currentPath, width=400)
    cmds.button(label="Browse", command=onBrowse)
    cmds.setParent('..')  # rowLayout を終了

    cmds.separator(h=8, style="none")

    # rowLayout を開始
    cmds.rowLayout(nc=3, cw3=(150, 50, 150), adj=1, cal=(1, "center"), cat=(1, "both", 5))
    cmds.button(label="Update", command=onOK)
    cmds.button(label="AddVer", command=onAddVer)
    cmds.button(label="Cancel", command=onCancel)
    cmds.setParent('..')  # rowLayout を終了

    cmds.showWindow(window)


def checkFileExistence(basePath, paths):
    """
    指定されたパスのリスト内のファイルがすべて存在するかを確認します。

    Args:
        basePath (str): 基本となるディレクトリパス
        paths (list): 確認するファイルのリスト

    Returns:
        tuple: (存在するファイルのリスト, 存在しないファイルのリスト)
    """
    existingFiles = []
    missingFiles = []

    print("## checkFileExistence")
    for path in paths:
        fullPath = os.path.join(basePath, path).replace("\\", "/")
        if os.path.exists(fullPath):
            existingFiles.append(fullPath)
            print(f"[ Exists ]: {fullPath}")
        else:
            missingFiles.append(fullPath)
            print(f"[ Missing ]: {fullPath}")
    print("")

    return existingFiles, missingFiles


def updateCustomStepStrings(guide, newPath, currentCommonPath):
    """
    新しいパスで指定文字列を置き換え、Mayaノード属性を更新します。

    Args:
        guide (str): 対象のガイドノード名
        newPath (str): 新しいパス
        currentCommonPath (str): 現在の共通パス
    """
    try:
        preCustomStepString = cmds.getAttr(f"{guide}.preCustomStep")
        postCustomStepString = cmds.getAttr(f"{guide}.postCustomStep")

        # パス文字列を置き換え
        preCustomStepString = preCustomStepString.replace(currentCommonPath, newPath)
        postCustomStepString = postCustomStepString.replace(currentCommonPath, newPath)

        # ファイルの存在確認
        prePaths = [item.split(" | ")[1] for item in preCustomStepString.split(",")]
        postPaths = [item.split(" | ")[1] for item in postCustomStepString.split(",")]

        _, missingFiles = checkFileExistence(newPath, prePaths + postPaths)
        if missingFiles:
            # ファイルが見つからない場合の選択肢
            result = cmds.confirmDialog(
                title="Missing Files",
                message="The following files are missing:\n\n" + "\n".join(missingFiles) +
                        "\n\nDo you want to continue with the changes?",
                button=["Continue", "Cancel"],
                defaultButton="Continue",
                cancelButton="Cancel",
                dismissString="Cancel",
                icon="warning"
            )
            if result == "Cancel":
                cmds.warning("Update process has been canceled by the user.")
                return

        cmds.setAttr(f"{guide}.preCustomStep", preCustomStepString, type="string")
        cmds.setAttr(f"{guide}.postCustomStep", postCustomStepString, type="string")

        cmds.confirmDialog(
            title="Success",
            message="Paths updated successfully.",
            button=["OK"],
            defaultButton="OK",
            icon="information"
        )

        print("## updateCustomStepStrings")
        print("[ Updated ] preCustomStepString:", preCustomStepString)
        print("[ Updated ] postCustomStepString:", postCustomStepString)
    except Exception as e:
        cmds.error(f"Failed to update custom step strings: {e}")


def main():
    """
    スクリプトのエントリーポイント。GUIを起動し、ユーザーの入力を処理します。
    """
    try:
        guide = findGuideNode()

        preCustomStepString = cmds.getAttr(f"{guide}.preCustomStep")
        postCustomStepString = cmds.getAttr(f"{guide}.postCustomStep")

        preCommonPath = extractCommonPath(preCustomStepString)
        postCommonPath = extractCommonPath(postCustomStepString)
        customStepString = f"preCustomStep | {preCommonPath},postCustomStep | {postCommonPath}"
        customCommonPath = extractCommonPath(customStepString)

        print(f"## extractCommonPath\nCurrent Common Path:\n    {customCommonPath}\n")

        showPathEditorDialog(
            customCommonPath,
            lambda newPath: updateCustomStepStrings(guide, newPath, customCommonPath)
        )
    except Exception as e:
        cmds.error(f"Error in main: {e}")

### ------------------------------------------------------ 

# 実行
if __name__ == "__main__":
    main()
