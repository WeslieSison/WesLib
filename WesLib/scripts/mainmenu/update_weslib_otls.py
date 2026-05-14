"""Direct Houdini menu script: update WesLib HDAs into $WESLIB/otls."""

from __future__ import print_function

import os
import tempfile
import urllib.error
import urllib.request
import zipfile


SOURCE_ZIP_URL = "https://github.com/WeslieSison/WesLib/archive/refs/heads/main.zip"
SOURCE_OTLS_MARKER = "/WesLib/otls/"
DESTINATION_OTLS = "$WESLIB/otls"

REQUEST_TIMEOUT = 60
USER_AGENT = "Houdini-WesLib-OTL-Updater"


def run():
    try:
        result = update_weslib_otls()
    except Exception as exc:
        message = "WesLib OTL update failed:\n{0}".format(exc)
        print(message)
        _show_houdini_message(message, error=True)
        raise

    message = (
        "WesLib OTL update finished.\n"
        "Added: {added}\n"
        "Updated: {updated}\n"
        "Unchanged: {unchanged}\n"
        "Destination: {destination}"
    ).format(**result)

    print(message)
    _show_houdini_message(message)
    return result


def update_weslib_otls():
    destination = _expand_path(DESTINATION_OTLS)
    if not _path_is_resolved(destination):
        raise RuntimeError("Cannot resolve {0}. Check that WESLIB is set.".format(DESTINATION_OTLS))

    if not os.path.isdir(destination):
        os.makedirs(destination)

    zip_path = _download_source_zip()
    try:
        result = _extract_otls(zip_path, destination)
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)

    if result["changed_files"]:
        _reload_houdini_hdas(result["changed_files"])

    return {
        "added": result["added"],
        "updated": result["updated"],
        "unchanged": result["unchanged"],
        "destination": DESTINATION_OTLS,
    }


def _download_source_zip():
    fd, zip_path = tempfile.mkstemp(prefix="weslib_", suffix=".zip")
    os.close(fd)

    request = urllib.request.Request(SOURCE_ZIP_URL, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            with open(zip_path, "wb") as handle:
                handle.write(response.read())
    except urllib.error.URLError as exc:
        if os.path.exists(zip_path):
            os.remove(zip_path)
        raise RuntimeError("Cannot download WesLib from GitHub: {0}".format(exc))

    return zip_path


def _extract_otls(zip_path, destination):
    result = {"added": 0, "updated": 0, "unchanged": 0, "changed_files": []}
    found = 0

    with zipfile.ZipFile(zip_path, "r") as archive:
        for member in archive.namelist():
            normalized = member.replace("\\", "/")
            marker_index = normalized.find(SOURCE_OTLS_MARKER)

            if marker_index < 0 or normalized.endswith("/"):
                continue

            rel_path = normalized[marker_index + len(SOURCE_OTLS_MARKER) :]
            if not rel_path:
                continue

            found += 1
            data = archive.read(member)
            target_path = _safe_join(destination, rel_path)
            status = _write_if_changed(target_path, data)

            result[status] += 1
            if status != "unchanged":
                result["changed_files"].append(target_path)
                print("{0}: {1}".format(status, rel_path))

    if found == 0:
        raise RuntimeError("No files found under WesLib/otls in the downloaded archive.")

    return result


def _write_if_changed(path, data):
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)

    existed = os.path.exists(path)
    if existed:
        with open(path, "rb") as handle:
            if handle.read() == data:
                return "unchanged"

    with open(path, "wb") as handle:
        handle.write(data)

    return "updated" if existed else "added"


def _reload_houdini_hdas(paths):
    try:
        import hou  # type: ignore
    except Exception:
        return

    try:
        if hasattr(hou.hda, "reloadAllFiles"):
            hou.hda.reloadAllFiles()
            return

        for path in paths:
            if path.lower().endswith((".hda", ".hdalc", ".otl", ".otllc")):
                hou.hda.installFile(path)
    except Exception as exc:
        print("Files were updated, but Houdini HDA reload failed: {0}".format(exc))


def _show_houdini_message(message, error=False):
    try:
        import hou  # type: ignore

        severity = hou.severityType.Error if error else hou.severityType.Message
        hou.ui.displayMessage(message, title="WesLib Update", severity=severity)
    except Exception:
        pass


def _expand_path(path):
    try:
        import hou  # type: ignore

        expanded = hou.expandString(path)
    except Exception:
        expanded = os.path.expandvars(path)

    return os.path.normpath(expanded)


def _path_is_resolved(path):
    return "$" not in path and "%" not in path


def _safe_join(root, rel_path):
    parts = []
    for part in rel_path.replace("\\", "/").split("/"):
        if not part or part in (".", ".."):
            raise RuntimeError("Unsafe path in archive: {0}".format(rel_path))
        parts.append(part)

    return os.path.join(root, *parts)



run()
