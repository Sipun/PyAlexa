#!/usr/bin/env python
import os
import subprocess
import zipfile
import sys
import getopt

"""
Script will create an AWS Lambda function deployment.

It expects there to be a deployments directory and it will create a
deployment of the form:

deployment_n

where n is incremented for each deployment based on the existing deployment
directories

If the AWS Lambda function has dependencies those dependencies are expected
to be in the requirements.txt file.

The implementation files are expected to be in the root project directory, and
this command does not currently support deeply nested file structures.

"""

root_deployments_dir = ''
root_project_dir = ''

# List of files that should be included in the deployment
# Only the files listed here, and the libraries in the requirements.txt
# file will be included in the deployment.
deployment_files = []


def _read_requirements():
    with open("{0}/requirements.txt".format(root_project_dir), 'r') as f:
        install_requirements = f.readlines()

    return install_requirements


def _get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]


def _mkdirp(directory):
    if not os.path.isdir(directory):
        os.makedirs(directory)


def _make_deployment_dir():
    _mkdirp(root_deployments_dir)
    all_deployment_directories = _get_immediate_subdirectories(root_deployments_dir)
    max_deployment_number = -1
    for deployment_dir in all_deployment_directories:
        dir_name_elements = deployment_dir.split("_")
        if (len(dir_name_elements) == 2):
            if int(dir_name_elements[1]) > max_deployment_number:
                max_deployment_number = int(dir_name_elements[1])

    if max_deployment_number == -1:
        max_deployment_number = 0

    deployment_name = "deployment_{0}".format(max_deployment_number + 1)
    new_deployment_dir_path = "{0}/{1}".format(root_deployments_dir, deployment_name)

    if not os.path.exists(new_deployment_dir_path):
        os.mkdir(new_deployment_dir_path)

    return (new_deployment_dir_path, deployment_name)


def _install_requirements(deployment_requirements, deployment_dir):
    """
    pip install <requirements line> -t <deployment_dir>
    :param deployment_requirements
    :param deployment_dir:
    :return:
    """
    if os.path.exists(deployment_dir):
        for requirement in deployment_requirements:
            if not requirement.startswith('#'):
                cmd = "pip install {0} -t {1}".format(requirement, deployment_dir).split()
                return_code = subprocess.call(cmd, shell=False)


def _copy_deployment_files(deployment_dir):
    for deployment_file in deployment_files:
        if os.path.exists(deployment_file):
            cmd = "cp {0} {1}".format(deployment_file, deployment_dir).split()
            return_code = subprocess.call(cmd, shell=False)
        else:
            raise NameError("Deployment file not found [{0}]".format(deployment_file))


def zipdir(dirPath=None, zipFilePath=None, includeDirInZip=False):
    """
    Attribution:  I wish I could remember where I found this on the
    web.  To the unknown sharer of knowledge - thank you.

    Create a zip archive from a directory.

    Note that this function is designed to put files in the zip archive with
    either no parent directory or just one parent directory, so it will trim any
    leading directories in the filesystem paths and not include them inside the
    zip archive paths. This is generally the case when you want to just take a
    directory and make it into a zip file that can be extracted in different
    locations.

    Keyword arguments:

    dirPath -- string path to the directory to archive. This is the only
    required argument. It can be absolute or relative, but only one or zero
    leading directories will be included in the zip archive.

    zipFilePath -- string path to the output zip file. This can be an absolute
    or relative path. If the zip file already exists, it will be updated. If
    not, it will be created. If you want to replace it from scratch, delete it
    prior to calling this function. (default is computed as dirPath + ".zip")

    includeDirInZip -- boolean indicating whether the top level directory should
    be included in the archive or omitted. (default True)

"""
    if not zipFilePath:
        zipFilePath = dirPath + ".zip"
    if not os.path.isdir(dirPath):
        raise OSError("dirPath argument must point to a directory. "
                      "'%s' does not." % dirPath)
    parentDir, dirToZip = os.path.split(dirPath)

    # Little nested function to prepare the proper archive path
    def trimPath(path):
        archivePath = path.replace(parentDir, "", 1)
        if parentDir:
            archivePath = archivePath.replace(os.path.sep, "", 1)
        if not includeDirInZip:
            archivePath = archivePath.replace(dirToZip + os.path.sep, "", 1)
        return os.path.normcase(archivePath)

    outFile = zipfile.ZipFile(zipFilePath, "w",
                              compression=zipfile.ZIP_DEFLATED)
    for (archiveDirPath, dirNames, fileNames) in os.walk(dirPath):
        for fileName in fileNames:
            filePath = os.path.join(archiveDirPath, fileName)
            outFile.write(filePath, trimPath(filePath))
        # Make sure we get empty directories as well
        if not fileNames and not dirNames:
            zipInfo = zipfile.ZipInfo(trimPath(archiveDirPath) + "/")
            # some web sites suggest doing
            # zipInfo.external_attr = 16
            # or
            # zipInfo.external_attr = 48
            # Here to allow for inserting an empty directory.  Still TBD/TODO.
            outFile.writestr(zipInfo, "")
    outFile.close()


def main(argv):
    global root_deployments_dir, root_project_dir
    include_files = ''

    try:
        opts, args = getopt.getopt(argv, "hr:i:", ["root=", "include="])
    except getopt.GetoptError:
        print 'create_aws_lambda.py -r <root project dir> -i <include files>'
        print 'if -r option not supplied it will look for PWD environment variable'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'create_aws_lambda.py -r <root project dir> -i <include files>'
            print 'if -r option not supplied it will look for PWD environment variable'
            print '<include files> are relative to root project dir'
            sys.exit()
        elif opt in ("-r", "--root"):
            root_project_dir = arg
        elif opt in ("-i", "--include"):
            include_files = arg

    if not root_project_dir:
        root_project_dir = os.environ.get("PWD")
        if root_project_dir is None:
            raise ValueError("Must supply -r or --root option")

    if not include_files:
        raise ValueError("Must supply -i or --include option")

    for include_file in include_files.split(","):
        deployment_files.append("{0}/{1}".format(root_project_dir,include_file.strip()))

    root_deployments_dir = "{0}/deployments".format(root_project_dir)
    (deployment_dir, deployment_name) = _make_deployment_dir()
    _copy_deployment_files(deployment_dir)
    install_requirements = _read_requirements()
    _install_requirements(install_requirements, deployment_dir)

    zipdir(deployment_dir, "{0}/{1}.zip".format(root_deployments_dir, deployment_name))


if __name__ == "__main__":
    main(sys.argv[1:])
