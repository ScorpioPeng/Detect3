import base64
import re
import shutil
import os
import datetime
import smtplib
import time
import zipfile
from datetime import date
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from tamper_noisetest import TamperInferenceConfig,modellib,detect,detect_zip
from PyQt5 import QtGui
from PyQt5.Qt import *
from dbtools import *
from resource.mainwindow import Ui_Form as mainwin
from resource.register_ui import Ui_Form as registerwin
from resource.login import Ui_Form as loginUi
from PIL import Image, ImageChops, ImageEnhance
dbfile='maskrcnn.db'

#路径信息
weights = "Model_maskrcnn/mask_rcnn_tamper_0220.h5"
dataset = "duibitu"
datasetzip='zipfiles'
predataset='predataset'
subset = "test"
logs = "logs"
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

# 模型导入
print("Weights: ", weights)
print("Dataset: ", dataset)
print("Subset: ", subset)
print("Logs: ", logs)
config = TamperInferenceConfig()
config.display()
model = modellib.MaskRCNN(mode="inference", config=config, model_dir=logs)
weights_path = weights
print("Loading weights ", weights_path)
model.load_weights(weights_path, by_name=True)
detect(model,predataset,subset)





def ela(fname, orig_dir, save_dir):
    quality = 90
    TMP_EXT = ".tmp_ela.jpg"
    ELA_EXT = ".jpg"

    basename, ext = os.path.splitext(fname)#图片名称tupian

    org_fname = os.path.join(orig_dir, fname)#/home/as/deeplab/wpmrcnn/ca2new/train/images/tupian.jpg
    tmp_fname = os.path.join(save_dir, basename + TMP_EXT) #/home/as/deeplab/wpmrcnn/ca2new/train/images/generated/tupian.tmp_ela.jpg
    ela_fname = os.path.join(save_dir, basename + ELA_EXT) #/home/as/deeplab/wpmrcnn/ca2new/train/images/generated/tupian.jpg

    im = Image.open(org_fname)
    im.save(tmp_fname, 'JPEG', quality=quality)

    tmp_fname_im = Image.open(tmp_fname)
    ela_im = ImageChops.difference(im, tmp_fname_im)

    extrema = ela_im.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    scale = 255.0/max_diff
    ela_im = ImageEnhance.Brightness(ela_im).enhance(scale)

    ela_im.save(ela_fname)
    os.remove(tmp_fname)

def mainela (dirc,ela_dirc):
    quality = 90
    print("Performing ELA on images at %s" % dirc)
    if not os.path.exists(ela_dirc):
        os.makedirs(ela_dirc)

    for d in os.listdir(dirc):
        if d.endswith(".tif") or d.endswith(".jpg") or d.endswith(".png"):
            ela(d,dirc,ela_dirc)

#注册界面
class Regiter_Win(QWidget,registerwin):
    def __init__(self):
        super().__init__()
        self.id=id
        self.setAttribute(Qt.WA_StyledBackground)  # 打开背景图片
        self.setupUi(self)
    def commit_info(self):
        if self.lineEdit.text() and self.lineEdit_2.text() and self.lineEdit_3.text() and self.lineEdit_4.text():
            if self.lineEdit.text():
                pass
            else:
                mess = QMessageBox(self)
                mess.setWindowTitle("警告")
                mess.setWindowIcon(QtGui.QIcon('resource/images/warning.png'))
                mess.addButton(self.tr("好的"), QMessageBox.YesRole)
                mess.setText('请填写账号！       ')
                mess.exec()
                return
            if self.verifyEmail(self.lineEdit_2.text()):
                pass
            else:
                self.lineEdit_2.setText('')
                return
            if self.lineEdit_3.text()!=self.lineEdit_4.text():
                mess = QMessageBox(self)
                mess.setWindowTitle("警告")
                mess.setWindowIcon(QtGui.QIcon('resource/images/warning.png'))
                mess.addButton(self.tr("好的"), QMessageBox.YesRole)
                mess.setText('两次输入的密码不一致！       ')
                mess.exec()
                self.lineEdit_3.setText('')
                self.lineEdit_4.setText('')
                return
            else:
                pass
            if self.lineEdit_5.text():
                pass
            else:
                mess = QMessageBox(self)
                mess.setWindowTitle("警告")
                mess.setWindowIcon(QtGui.QIcon('resource/images/warning.png'))
                mess.addButton(self.tr("好的"), QMessageBox.YesRole)
                mess.setText('请输入您的姓名，谢谢！       ')
                mess.exec()
                return
            if self.lineEdit_6.text():
                pass
            else:
                mess = QMessageBox(self)
                mess.setWindowTitle("警告")
                mess.setWindowIcon(QtGui.QIcon('resource/images/warning.png'))
                mess.addButton(self.tr("好的"), QMessageBox.YesRole)
                mess.setText('请填写您的工作单位！       ')
                mess.exec()
                return


            uId=self.lineEdit.text()
            password=self.lineEdit_3.text()
            email=self.lineEdit_2.text()
            name=self.lineEdit_5.text()
            institute=self.lineEdit_6.text()
            if uId and password and email:  # 防止空输入
                conn = get_db_conn(dbfile)
                cur1 = conn.cursor()
                sql1 = 'select * from user where userid=?'
                cur1.execute(sql1, (uId,))
                result = cur1.fetchone()
                # print(result)
                if result != None:
                    # QMessageBox.warning(self, '注册账号', '账号已存在，请重新注册', QMessageBox.Yes)
                    mess = QMessageBox(self)
                    mess.setWindowTitle("警告")
                    mess.setWindowIcon(QtGui.QIcon('resource/images/warning.png'))
                    mess.addButton(self.tr("好的"), QMessageBox.YesRole)
                    mess.setText('账号已存在，请重新注册       ')
                    mess.exec()
                    self.lineEdit.setText("")
                    self.lineEdit_2.setText("")
                    self.lineEdit_3.setText("")
                    self.lineEdit_4.setText("")
                    cur1.close()
                else:
                    cur1.close()
                    cur2 = conn.cursor()
                    sql2 = 'insert into user (userid,password,email,name,institute) values (?,?,?,?,?)'
                    data = (uId, password,email,name,institute,)
                    cur2.execute(sql2, data)
                    conn.commit()
                    # 对话框
                    mess = QMessageBox(self)
                    mess.setWindowTitle("注册账号")
                    mess.setWindowIcon(QtGui.QIcon('resource/images/ok.png'))
                    mess.addButton(self.tr("好的"), QMessageBox.YesRole)
                    mess.setText('账号注册成功！       ')
                    self.lineEdit.setText("")
                    self.lineEdit_2.setText("")
                    self.lineEdit_3.setText("")
                    self.lineEdit_4.setText("")
                    self.lineEdit_5.setText("")
                    self.lineEdit_6.setText("")
                    mess.exec()
                    # QMessageBox.information(self, '注册账号', '注册成功', QMessageBox.Yes)
                    cur2.close()
                    print("插入成功")
                conn.close()
        else:
            mess = QMessageBox(self)
            mess.setWindowTitle("警告")
            mess.setWindowIcon(QtGui.QIcon('resource/images/warning.png'))
            mess.addButton(self.tr("好的"), QMessageBox.YesRole)
            mess.setText('请填写正确的注册信息!      ')
            mess.exec()


    def back(self):
        self.hide()
        self.loginwin=LoginPane()
        self.loginwin.show()

    def verifyEmail(self,email):

        pattern = r'^[0-9a-zA-Z_]{0,19}@[0-9a-zA-Z]{1,13}\.[com,cn,net]{1,3}$'

        # 使用re库的match方法校验传入的邮箱参数是否合理,是否与表达式匹配

        if re.match(pattern, email) is not None:
            print("输入邮箱正确")
            return True
        else:
            print('输入的地址无效')
            mess = QMessageBox(self)
            mess.setWindowTitle("警告")
            mess.setWindowIcon(QtGui.QIcon('resource/images/warning.png'))
            mess.addButton(self.tr("好的"), QMessageBox.YesRole)
            mess.setText('邮箱不正确       ')
            mess.exec()
            return False


#登录界面
class LoginPane(QWidget,loginUi):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_StyledBackground)     #打开背景图片
        self.setupUi(self)


    def register(self):
        self.registerwin=Regiter_Win()
        self.hide()
        self.registerwin.show()


    def check_login(self):

        uId=self.Account_lineEdit.text()
        password=self.Password_lineEdit.text()
        if uId and password:  # 防止空输入
            #获取数据库连接
            conn=get_db_conn(dbfile)
            cur1 = conn.cursor()
            sql1 = 'select * from user where userid=?'
            cur1.execute(sql1, (uId,))
            result = cur1.fetchone()
            # print(result)
            if result == None:
                #对话框
                mess=QMessageBox(self)
                mess.setWindowTitle("登录账号")
                mess.setWindowIcon(QtGui.QIcon('resource/images/error.png'))
                mess.addButton(self.tr("好的"), QMessageBox.YesRole)
                mess.setText('该账号尚未注册,请先注册！       ')
                mess.exec()
                self.Password_lineEdit.setText("")
                # QMessageBox.warning(self, '登录', '该账号尚未注册,请先注册')
            else:
                if result[1]!=password:
                    mess = QMessageBox(self)
                    mess.setWindowTitle("登录账号")
                    mess.setWindowIcon(QtGui.QIcon('resource/images/error.png'))
                    mess.addButton(self.tr("好的"), QMessageBox.YesRole)
                    mess.setText('密码错误，请重新输入！       ')
                    self.Password_lineEdit.setText("")
                    mess.exec()
                    # QMessageBox.critical(self, '登录', '密码错误')
                else:
                    email=result[2]
                    name=result[3]
                    institute=result[4]
                    self.hide()
                    self.mainwindow=Main_Window(uId,email,name,institute)
                    self.mainwindow.show()
                    close_db_conn(cur1,conn)

#主业务窗口
class Main_Window(QWidget,mainwin):
    def __init__(self,id,email,name,institute):
        super().__init__()
        self.id=id
        self.email=email
        self.name=name
        self.institute=institute
        self.setAttribute(Qt.WA_StyledBackground)  # 打开背景图片
        self.setupUi(self)
        self.Id_label.setText(self.id)
        self.Id_label_3.setText(self.email)
        self.nametiltelabel.setText(name)
        self.institutelabel.setText(institute)
        self.email_lineEdit.setText(email)
        #使用动态图
        self.waitgif = QMovie('resource/images/wait.gif')
        self.gif_label.setMovie(self.waitgif)
        #下载按钮禁用
        self.start_detect_btn_2.setEnabled(False)
        self.pushButton_3.setEnabled(False)


    #修改密码
    def change_password(self):
        pass1=self.newpass_lineedit.text()
        pass2=self.newpass_con_lineedit.text()
        if pass1 and pass2:
            if pass1!=pass2:
                # 密码不一致对话框
                mess = QMessageBox(self)
                mess.setWindowTitle("修改密码")
                mess.setWindowIcon(QtGui.QIcon('resource/images/error.png'))
                mess.addButton(self.tr("好的"), QMessageBox.YesRole)
                mess.setText('两次输入密码不一致！       ')
                mess.exec()
                #新密码不一致，重置输入框
                self.newpass_lineedit.setText("")
                self.newpass_con_lineedit.setText("")
            else:
                #新密码一致
                conn=get_db_conn(dbfile)
                cur=conn.cursor()
                sql='update user set password=? where userid=?'
                data=(pass1,self.id,)
                cur.execute(sql,data)
                conn.commit()
                close_db_conn(cur,conn)
                mess = QMessageBox(self)
                mess.setWindowTitle("修改密码")
                mess.setWindowIcon(QtGui.QIcon('resource/images/ok.png'))
                mess.addButton(self.tr("好的"), QMessageBox.YesRole)
                mess.setText('密码修改成功！       ')
                mess.exec()
                #修改完重置输入框
                self.newpass_con_lineedit.setText('')
                self.newpass_lineedit.setText('')

    #退出登录
    def back(self):
        self.loginp=LoginPane()
        self.hide()
        self.loginp.show()

    #上传篡改图像
    def upload_tamper(self):

        #下载按钮禁用
        self.start_detect_btn_2.setEnabled(False)
        #结果图清空
        self.result_pic.clear()

        result_dis='results/one'
        self.setDir(result_dis)
        tampername,_=QFileDialog.getOpenFileName(self,"上传篡改图像",'D:\wpmaskrcnn\duibitu\\',"Image Files(*.png *.jpg *.tif)")
        self.tamper_pic.setPixmap(QPixmap(tampername))
        self.tamper_pic.setScaledContents(True)
        self.tamper_pic_addr.setText(tampername)
        print(tampername)
        dist='duibitu/test/images/'
        ela_dist='duibitu/test/elas/'
        if  os.path.isfile(tampername):
            self.setDir(dist)
            disname=self.mymovefile(tampername,dist)
            print(disname)
            # os.rename(disname,dist+"example.jpg")

            #生成ela
            mainela(dist,ela_dist)


    #开始检测单张图像
    def start_detect(self):
        tamper_dir='duibitu/test/images/'
        ela_dir='duibitu/test/elas'
        dirs=os.listdir(tamper_dir)

        if os.listdir(tamper_dir) and os.listdir(ela_dir):
            tamper = tamper_dir + dirs[0]
            start_time=datetime.datetime.now().replace(microsecond=0)
            detect(model,dataset,subset)
            end_time=datetime.datetime.now().replace(microsecond=0)
            extime=(end_time-start_time).seconds
            f=os.listdir('results/one')
            pic='results/one/'+f[0]
            self.result_pic.setPixmap(QPixmap(pic))
            self.result_pic.setScaledContents(True)
            (filename, extension) = os.path.splitext(f[0])

            #将图片转码
            with open(tamper, 'rb') as f:
                res = base64.b64encode(f.read())
            with open(pic, 'rb') as f2:
                res2 = base64.b64encode(f2.read())

            #存入数据库
            sql='insert into piclogs (userid,timett,imagename,tamper,result) values (?,?,?,?,?)'
            data=(self.id,start_time,filename,res,res2,)
            conn=get_db_conn(dbfile)
            cur=conn.cursor()
            cur.execute(sql,data)
            conn.commit()
            close_db_conn(cur,conn)
            print("检测数据库更新完")

            self.setDir(tamper_dir)
            self.setDir(ela_dir)
            self.start_detect_btn_2.setEnabled(True)
        else:
            if not os.listdir(tamper_dir):
                mess=QMessageBox(self)
                mess.setWindowTitle("警告")
                mess.setWindowIcon(QtGui.QIcon('resource/images/warning.png'))
                mess.addButton(self.tr("好的"), QMessageBox.YesRole)
                mess.setText('请上传篡改图像       ')
                mess.exec()
            else:
                pass

    #保存数据库图片
    def download_db(self):
        filepath = QFileDialog.getExistingDirectory(self, "选择保存路径", 'D:/')
        if filepath:
            root='dbpic/result'
            files=os.listdir(root)
            for file in files:
                f=os.path.join(root,file)
                self.mymovefile(f,filepath)
            mess = QMessageBox(self)
            mess.setWindowTitle("批量保存")
            mess.setWindowIcon(QtGui.QIcon('resource/images/ok.png'))
            mess.addButton(self.tr("好的"), QMessageBox.YesRole)
            mess.setText('成功下载最近的10张定位图片！       ')
            mess.exec()
            self.pushButton_3.setEnabled(False)
        else:
            pass

    def download_one(self):
        src_path='results/one'
        f=os.listdir(src_path)[0]
        filepath=QFileDialog.getExistingDirectory(self,"选择保存路径",'D:/')
        if filepath:
            src_file=os.path.join(src_path,f)
            self.mymovefile(src_file,filepath)
            self.start_detect_btn_2.setEnabled(False)
            mess = QMessageBox(self)
            mess.setWindowTitle("保存")
            mess.setWindowIcon(QtGui.QIcon('resource/images/ok.png'))
            mess.addButton(self.tr("好的"), QMessageBox.YesRole)
            mess.setText('成功保存当前定位结果！       ')
            mess.exec()
        else:
            pass


    #上传篡改压缩包
    def upload_tamper_zip(self):
        tamper_zip_name, _ = QFileDialog.getOpenFileName(self, "上传篡改图像压缩包", 'D:\wpmaskrcnn\duibitu\\', "All Files (*)")
        print(tamper_zip_name)
        self.tamper_addr.setText(tamper_zip_name)
        dist='zipfiles/test/images/'
        ela_dist='zipfiles/test/elas/'
        if not os.path.exists(dist):
            os.makedirs(dist)
        if os.path.isfile(tamper_zip_name):
            self.setDir(dist)
            self.unzip_file(tamper_zip_name,dist)
        mainela(dist,ela_dist)


    #上传ELA压缩包
    def upload_ela_zip(self):
        ela_zip_name, _ = QFileDialog.getOpenFileName(self, "上传ELA图像压缩包", 'D:\wpmaskrcnn\duibitu\\', "All Files (*)")
        print(ela_zip_name)
        self.ela_addr.setText(ela_zip_name)
        dist='zipfiles/test/elas/'
        if not os.path.exists(dist):
            os.makedirs(dist)
        if os.path.isfile(ela_zip_name):
            self.setDir(dist)
            self.unzip_file(ela_zip_name,dist)



    #循环调用检测模型
    def strat_multi_detect(self):
        zip_tamper="zipfiles/test/images/"
        zip_ela="zipfiles/test/elas/"
        one_tamper='duibitu/test/images/'
        one_ela='duibitu/test/elas/'
        result_dist='results/one'
        self.setDir(result_dist)
        email_dist = self.email_lineEdit.text()
        if os.listdir(zip_tamper) and os.listdir(zip_ela):
            if self.verifyEmail(email_dist):
                #当前界面按钮禁用
                self.btn_email.setEnabled(False)
                self.btn_tamper_zip.setEnabled(False)
                #先清空结果文件夹
                self.setDir(result_dist)
                #1动态图开始动
                self.gif_label.setVisible(True)
                self.waitgif.start()

                # self.dialog.show()#2弹出动图对话框

                # #启动线程，检测完毕发出signal信号，连接到zip_send槽函数
                # self.thread=ZipThread(email_dist)
                # self.thread.signal.connect(self.zip_send)
                # self.thread.start()
                count=1
                length=len(os.listdir(zip_tamper))
                self.total_label.setText(str(length))
                #循环调用
                for i in range(len(os.listdir(zip_tamper))):
                    self.setDir(one_tamper)
                    self.setDir(one_ela)
                    tamper=os.listdir(zip_tamper)[i]
                    ela=os.listdir(zip_ela)[i]
                    tamper_path=zip_tamper+tamper
                    ela_path=zip_ela+ela
                    self.running_label.setText(tamper)
                    self.num_comp_label.setText(str(count))
                    fname=self.mymovefile(tamper_path,one_tamper)
                    fname_ela=self.mymovefile(ela_path,one_ela)
                    print("正在处理： "+fname+" 和 "+fname_ela)
                    detect(model,dataset,subset)
                    count=count+1
                    QApplication.processEvents()
                    time.sleep(0.1)

                print("全部检测完毕，开始打包发邮件")
                self.running_label.setText("")

                #打包结果
                self.zip_file(result_dist)
                self.email_zip(email_dist)
                os.remove('results/one.zip')
                self.setDir(zip_tamper)
                self.setDir(zip_ela)
                self.setDir(one_tamper)
                self.setDir(one_ela)
                self.setDir(result_dist)
                print("邮件结束")
                self.zip_send()
            else:
                pass
        else:
            mess = QMessageBox(self)
            mess.setWindowTitle("警告")
            mess.setWindowIcon(QtGui.QIcon('resource/images/warning.png'))
            mess.addButton(self.tr("好的"), QMessageBox.YesRole)
            mess.setText('请上传篡改图像压缩包       ')
            mess.exec()



    #弹出邮箱发送完毕窗口
    def zip_send(self):
        self.waitgif.stop()
        self.gif_label.setVisible(False)
        mess = QMessageBox(self)
        mess.setWindowTitle("邮件")
        mess.setWindowIcon(QtGui.QIcon('resource/images/ok.png'))
        mess.addButton(self.tr("好的"), QMessageBox.YesRole)
        mess.setText('定位结果邮件已发送至'+self.email_lineEdit.text()+'!       ')
        mess.exec()
        self.btn_email.setEnabled(True)
        self.btn_tamper_zip.setEnabled(True)
        ##弹出对话框方法
        # self.dialog.close()
        # mess = QMessageBox(self)
        # mess.setWindowTitle("修改密码")
        # mess.setWindowIcon(QtGui.QIcon('resource/images/ok.png'))
        # mess.addButton(self.tr("好的"), QMessageBox.YesRole)
        # mess.setText('定位结果邮件已发送！       ')
        # mess.exec()

    #查看历史记录
    def check_logs(self):
        path_1='dbpic/tamper/'
        path_2='dbpic/result/'
        self.setDir(path_1)
        self.setDir(path_2)
        conn=get_db_conn(dbfile)
        cur=conn.cursor()
        sql='select * from piclogs where userid=? order by timett desc'
        data=(self.id,)
        cur.execute(sql,data)
        result = cur.fetchall()
        if len(result)!=0:
            row=len(result)
            vol=4
            if row<=10:
                self.tableWidget.setRowCount(row)
                self.tableWidget.setColumnCount(vol)
            else:
                row=10
                self.tableWidget.setRowCount(row)
                self.tableWidget.setColumnCount(vol)

            self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.tableWidget.setHorizontalHeaderLabels(['提交检测时间','图像名称','篡改图像','定位结果'])

            for i in range(row):
                #处理文字信息
                for j in range(vol-2):#前两列
                    temp_data = result[i][j+1]  # 临时记录，不能直接插入表格
                    data = QTableWidgetItem(str(temp_data))  # 转换后可插入表格
                    self.tableWidget.setItem(i, j, data)

                #处理篡改图像
                imagename=result[i][2]
                tampercode=result[i][3]
                tamper=base64.b64decode(tampercode)
                time1=str(result[i][1]).replace(':','-')
                tamper_name='dbpic/tamper/'+imagename+'_'+time1+'.jpg'
                file=open(tamper_name,'wb')
                file.write(tamper)
                file.close()
                label=QLabel()
                label.setPixmap(QPixmap(tamper_name).scaled(150,150))
                hlayout=QHBoxLayout()
                hlayout.addWidget(label)
                hlayout.setAlignment(label,Qt.AlignCenter)
                widget=QWidget()
                widget.setLayout(hlayout)
                self.tableWidget.setCellWidget(i,2,widget)

                #处理定位图像
                resultcode=result[i][4]
                resultpic=base64.b64decode(resultcode)
                result_name='dbpic/result/'+imagename+'_'+time1+'.jpg'
                file=open(result_name,'wb')
                file.write(resultpic)
                file.close()
                label2=QLabel()
                label2.setPixmap(QPixmap(result_name).scaled(150,150))
                hlayout2=QHBoxLayout()
                hlayout2.addWidget(label2)
                hlayout2.setAlignment(label2,Qt.AlignCenter)
                widget2=QWidget()
                widget2.setLayout(hlayout2)
                self.tableWidget.setCellWidget(i,3,widget2)
            self.pushButton_3.setEnabled(True)

            close_db_conn(cur, conn)

            for i in range(row):
                self.tableWidget.setRowHeight(i,150)
                for j in range(vol-2):
                    self.tableWidget.setColumnWidth(j, 150)
                    self.tableWidget.item(i,j).setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)


        else:
            close_db_conn(cur,conn)


    #移动文件到指定文件夹下
    def mymovefile(self,srcfile, dstpath):  # 移动函数
        if not os.path.isfile(srcfile):
            print("%s not exist!" % (srcfile))
        else:
            fpath, fname = os.path.split(srcfile)  # 分离文件名和路径
            if not os.path.exists(dstpath):
                os.makedirs(dstpath)  # 创建路径
            path=os.path.join(dstpath,fname)
            shutil.copy(srcfile,path)  # 移动文件
            print("移动 %s 到 %s" % (srcfile, path))
        #返回目的地址路径+名称
        return path


    #清空文件夹
    def setDir(self,filepath):
        '''
        如果文件夹不存在就创建，如果文件存在就清空！
        :param filepath:需要创建的文件夹路径
        :return:
        '''
        if not os.path.exists(filepath):
            os.mkdir(filepath)
        else:
            shutil.rmtree(filepath)
            os.mkdir(filepath)

    #解压文件到指定目录
    def unzip_file(self,zip_src, dst_dir):
        temp = 'temp'
        if not os.path.exists(temp):
            os.mkdir(temp)
        r = zipfile.is_zipfile(zip_src)
        if r:
            fz = zipfile.ZipFile(zip_src, 'r')
            for file in fz.namelist():
                fz.extract(file, temp)
            for root, dirs, files in os.walk(temp):
                pass
            files = os.listdir(root)
            for i in files:
                print(i)
                shutil.move(os.path.join(root, i), dst_dir)
            self.setDir(temp)
        else:
            print('This is not zip')

    # def unzip_file(self,zip_src, dst_dir):
    #     r = zipfile.is_zipfile(zip_src)
    #     if r:
    #         fz = zipfile.ZipFile(zip_src, 'r')
    #         for file in fz.namelist():
    #             fz.extract(file, dst_dir)
    #     else:
    #         print('This is not zip')

    def zip_file(self,src_dir):
        zip_name = src_dir +'.zip'
        z = zipfile.ZipFile(zip_name,'w',zipfile.ZIP_DEFLATED)
        for dirpath, dirnames, filenames in os.walk(src_dir):
            fpath = dirpath.replace(src_dir,'')
            fpath = fpath and fpath + os.sep or ''
            for filename in filenames:
                z.write(os.path.join(dirpath, filename),fpath+filename)
                print ('==压缩成功==')
        z.close()

    def email_zip(self,email):
        # 获取今天日期
        today = date.today()
        date_today = today.strftime("%m%d")
        # 发送邮件
        global msg_list
        msg_list = MIMEMultipart()
        msg_list['From'] = '1695100184@qq.com'
        msg_list['To'] = email
        msg_list['Subject'] = '检测结果' + date_today
        body = '数字图像篡改定位系统检测结果' + date_today
        msg_list.attach(MIMEText(body))
        with open("results/one.zip", 'rb') as f:
            # 附件的MIME和文件名
            mime = MIMEBase('zip', 'zip', filename='检测结果.zip')
            # 加上必要的头信息
            mime.add_header('Content-Disposition', 'attachment', filename=('gb2312', '', '检测结果.zip'))
            mime.add_header('Content-ID', '<0>')
            mime.add_header('X-Attachment-Id', '0')
            # 把附件的内容读进来
            mime.set_payload(f.read())
            # 用Base64编码
            encoders.encode_base64(mime)
            msg_list.attach(mime)

        server = smtplib.SMTP('smtp.qq.com')
        server.starttls()
        fromAddr = '1695100184@qq.com'  # 发件人
        myPass = 'ybjxryrlgedededc'  # 发件人密码
        server.login(fromAddr, myPass)
        server.send_message(msg_list)
        server.quit()
        print(">>>发送邮件成功！")

    def verifyEmail(self,email):

        pattern = r'^[0-9a-zA-Z_]{0,19}@[0-9a-zA-Z]{1,13}\.[com,cn,net]{1,3}$'

        # 使用re库的match方法校验传入的邮箱参数是否合理,是否与表达式匹配

        if re.match(pattern, email) is not None:
            print("输入邮箱正确")
            return True
        else:
            print('输入的地址无效')
            mess = QMessageBox(self)
            mess.setWindowTitle("警告")
            mess.setWindowIcon(QtGui.QIcon('resource/images/warning.png'))
            mess.addButton(self.tr("好的"), QMessageBox.YesRole)
            mess.setText('邮箱不正确       ')
            mess.exec()
            return False

#线程
class ZipThread(QThread):
    signal = pyqtSignal()
    def __init__(self,address):
        super().__init__()
        self.address=address
    def run(self):
        detect_zip(model,datasetzip,subset)
        zip_tamper="zipfiles/test/images"
        zip_ela="zipfiles/test/elas"
        result_dist='results/multi'
        email_dist = self.address
        self.zip_file(result_dist)
        self.email_zip(email_dist)
        os.remove('results/multi.zip')
        self.setDir(zip_tamper)
        self.setDir(zip_ela)
        print("邮件结束")
        self.signal.emit()

    #压缩文件
    def zip_file(self,src_dir):
        zip_name = src_dir +'.zip'
        z = zipfile.ZipFile(zip_name,'w',zipfile.ZIP_DEFLATED)
        for dirpath, dirnames, filenames in os.walk(src_dir):
            fpath = dirpath.replace(src_dir,'')
            fpath = fpath and fpath + os.sep or ''
            for filename in filenames:
                z.write(os.path.join(dirpath, filename),fpath+filename)
                print ('==压缩成功==')
        z.close()

    #用邮件发送压缩包
    def email_zip(self,email):
        # 获取今天日期
        today = date.today()
        date_today = today.strftime("%m%d")
        # 发送邮件
        global msg_list
        msg_list = MIMEMultipart()
        msg_list['From'] = '1695100184@qq.com'
        msg_list['To'] = email
        msg_list['Subject'] = '检测结果' + date_today
        body = '检测结果' + date_today
        msg_list.attach(MIMEText(body))
        with open("results/multi.zip", 'rb') as f:
            # 附件的MIME和文件名
            mime = MIMEBase('zip', 'zip', filename='检测结果.zip')
            # 加上必要的头信息
            mime.add_header('Content-Disposition', 'attachment', filename=('gb2312', '', '检测结果.zip'))
            mime.add_header('Content-ID', '<0>')
            mime.add_header('X-Attachment-Id', '0')
            # 把附件的内容读进来
            mime.set_payload(f.read())
            # 用Base64编码
            encoders.encode_base64(mime)
            msg_list.attach(mime)

        server = smtplib.SMTP('smtp.qq.com')
        server.starttls()
        fromAddr = '1695100184@qq.com'  # 发件人
        myPass = 'ybjxryrlgedededc'  # 发件人密码
        server.login(fromAddr, myPass)
        server.send_message(msg_list)
        server.quit()
        print(">>>发送邮件成功！")

    #清空文件夹
    def setDir(self,filepath):
        '''
        如果文件夹不存在就创建，如果文件存在就清空！
        :param filepath:需要创建的文件夹路径
        :return:
        '''
        if not os.path.exists(filepath):
            os.mkdir(filepath)
        else:
            shutil.rmtree(filepath)
            os.mkdir(filepath)



if __name__=='__main__':
    import sys
    app=QApplication(sys.argv)
    window=LoginPane()
    window.setWindowIcon(QIcon("resource/images/icon.png"))
    window.show()

    sys.exit(app.exec())
