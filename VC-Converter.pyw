import threading
import time
import wx
import glob, os
import subprocess
import shutil

ext=".wav"
OutExt="mp3"
DAC=True
step=0
steps=[]
Total=0.0
n=0
IsRunning=False
sessions=[]
FirstTurn=[]
SecondTurn=[]
programpath=os.getcwd()
zippath=programpath+"\\zip files"
introsilence=0

def FileConvert(ses):
	global IsRunning
	global n
	n=0
	SetConfiguration()
	for s in ses:
		n+=1
		frm.tStatus.SetValue("در حال تبدیل فایل "+s.replace(programpath+"\\zip files\\", "")+"، فایل "+str(n)+" از "+str(len(sessions)))
		global FirstTurn
		FirstTurn=[]
		global SecondTurn
		SecondTurn=[]
		global step
		step=0
		InitializeFirstTurn(s)
		FindMute(s)
		frm.pPercent.SetValue(0)
		vFileConvert(FirstTurn[:], SecondTurn[:])
		while len(FirstTurn)+len(SecondTurn)>1:
			r=FirstAndSecondAnalyzer(FirstTurn, SecondTurn)
			FirstTurn=r[0]
			SecondTurn=r[1]
			if len(FirstTurn)==0:
				tSecondTurn=[]
				rst=[]
				for i in range(len(SecondTurn)):
					if SecondTurn[i][3] > 0:
						cmd="ffmpeg -y -f lavfi -i anullsrc=r=22050 -t "+str(SecondTurn[i][3])+"ms \""+s+"\\s"+str(i)+ext+"\""
						outp=subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
						while True:
							if outp.poll() is not None:
								frm.pPercent.SetValue(int(100*steps[step]/Total))
								step+=1
								break
							time.sleep(0.1)
						cmd="ffmpeg -y -i \""+s+"\\s"+str(i)+ext+"\" -i \""+s+"\\"+SecondTurn[i][1]+"\" -filter_complex \"[0:a][1:a] concat=n=2:v=0:a=1 [a]\" -map \"[a]\" \""+s+"\\m"+SecondTurn[i][1].replace(".flv", "")+ext+"\""
						outp=subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
						while True:
							l1=outp.stdout.readline().decode("utf-8")
							if outp.poll() is not None:
								frm.pPercent.SetValue(int(100*steps[step]/Total))
								step+=1
								break
							time.sleep(0.1)
						res=[0]
						res.append("m"+SecondTurn[i][1].replace(".flv", "")+ext+"")
						res.append(SecondTurn[i][2]+SecondTurn[i][3])
						res.append(0)
						rst.append(i)
						tSecondTurn.append(res)
				SecondTurn+=tSecondTurn
				for i in range(len(rst)-1, -1, -1):
					SecondTurn.pop(rst[i])
				break
			SecondTurn.append(MergeFiles(FirstTurn, s))
			FirstTurn=[]
			r=FirstAndSecondAnalyzer(SecondTurn, FirstTurn)
			SecondTurn=r[0]
			FirstTurn=r[1]
			if len(SecondTurn)==0:
				tFirstTurn=[]
				rst=[]
				for i in range(len(FirstTurn)):
					if FirstTurn[i][3] > 0:
						cmd="ffmpeg -y -f lavfi -i anullsrc=r=22050 -t "+str(FirstTurn[i][3])+"ms \""+s+"\\s"+str(i)+ext+"\""
						outp=subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
						while True:
							if outp.poll() is not None:
								frm.pPercent.SetValue(int(100*steps[step]/Total))
								step+=1
								break
							time.sleep(0.1)
						cmd="ffmpeg -y -i \""+s+"\\s"+str(i)+ext+"\" -i \""+s+"\\"+FirstTurn[i][1]+"\" -filter_complex \"[0:a][1:a] concat=n=2:v=0:a=1 [a]\" -map \"[a]\" \""+s+"\\m"+FirstTurn[i][1].replace(".flv", "")+ext+"\""
						outp=subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
						while True:
							l1=outp.stdout.readline().decode("utf-8")
							if outp.poll() is not None:
								frm.pPercent.SetValue(int(100*steps[step]/Total))
								step+=1
								break
							time.sleep(0.1)
						res=[0]
						res.append("m"+FirstTurn[i][1].replace(".flv", "")+ext+"")
						res.append(FirstTurn[i][2]+FirstTurn[i][3])
						res.append(0)
						rst.append(i)
						tFirstTurn.append(res)
				FirstTurn+=tFirstTurn
				for i in range(len(rst)-1, -1, -1):
					FirstTurn.pop(rst[i])
				break
			FirstTurn.append(MergeFiles(SecondTurn, s))
			SecondTurn=[]
		if len(FirstTurn)>0:
			inp=FirstTurn
		else:
			inp=SecondTurn
		cmd="ffmpeg -y "
		for i in range(len(inp)):
			cmd+="-i \""+s+"\\"+inp[i][1]+"\" "
		cmd+="-filter_complex amix=inputs="+str(len(inp))+":duration=longest \""+s.replace("zip files", "mp3 files")+"."+OutExt+"\""
		outp=subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		#print("mixing process has started")
		l1=outp.stdout.readline()
		while True:
			l1=outp.stdout.readline().decode("utf-8")
			if outp.poll() is not None:
				frm.pPercent.SetValue(int(100*steps[step]/Total))
				step+=1
				break
			time.sleep(0.1)
		shutil.rmtree(s)
		if DAC == True:
			os.remove(s+".zip")
	mFinish=wx.MessageDialog(frm, "عملیات تبدیل به پایان رسید", caption="پایان")
	mFinish.ShowModal()
	frm.tStatus.SetValue("")
	IsRunning=False

def UnzipArchives():
	global sessions
	sessions=[]
	os.chdir(".\\zip files")
	files=glob.glob("*.zip")
	for z in files:
		shutil.unpack_archive(z, z.replace(".zip", ""))
		sessions.append(os.getcwd()+"\\"+z.replace(".zip", ""))
	os.chdir(programpath)

def ConvertTime(time):
	res=0
	s1=time.split(".")
	res=res+int(s1[1])
	s2=s1[0].split(":")
	res=res+int(s2[0])*3600000+int(s2[1])*60000+int(s2[2])*1000
	return res

def FindTime(p, n):
	res=0
	tl=""
	f=open(p+"\\indexstream.xml", "r")
	lines=f.read().split("\n")
	for l in range(len(lines)):
		if n in lines[l]:
			tl=lines[l-2]
			break
	time=tl[tl.index("A[")+2:tl.index("]]")]
	return int(time)

def FindMute(p):
	global FirstTurn
	global introsilence
	n="stopStream"
	res=0
	tl=""
	f=open(p+"\\mainstream.xml", "r")
	lines=f.read().split("\n")
	for l in range(len(lines)):
		if n in lines[l]:
			tl=lines[l-7]
			nl=lines[l+2]
			time=int(tl[tl.index("time=\"")+6:tl.index("\" type")]) - introsilence
			StreamNumber=nl[nl.index("A[")+2:nl.index("]]")].split("_")[1]
			for i in range(len(FirstTurn)):
				FileNumber=FirstTurn[i][1].split("_")[1]
				if FileNumber == StreamNumber and FirstTurn[i][3] < time and time < FirstTurn[i][3]+FirstTurn[i][2]:
					#print("mute found in time "+str(time)+" in stream "+StreamNumber+": "+str(FirstTurn[i]))
					for j in range(l+1, len(lines)):
						if "playStream" in lines[j]:
							ptl=lines[j-7]
							time2=int(ptl[ptl.index("time=\"")+6:ptl.index("\" type")]) - introsilence
							pl=lines[j+2]
							PlayStreamNumber=pl[pl.index("A[")+2:pl.index("]]")].split("_")[1]
							if PlayStreamNumber == FileNumber and FirstTurn[i][3] < time2 and time2 < FirstTurn[i][3]+FirstTurn[i][2]:
								print("file "+FirstTurn[i][1]+", from "+str(time)+" to "+str(time2))
								break
	return time

def Sort2D(l, i, r=True):
	a=[]
	res=[]
	for s in l:
		a.append(s[i])
	oi=a[:]
	a.sort(reverse=r)
	for b in a:
		f=oi.index(b)
		res.append(l[f])
		l.pop(f)
		oi.pop(f)
	return res

def InitializeFirstTurn(s):
	global FirstTurn
	FirstTurn=[]
	os.chdir(s)
	files=glob.glob("cameravoip*.flv")
	os.chdir(programpath)
	times=[]
	for i in range(len(files)):
		ft=[]
		ft.append(i)
		ft.append(files[i])
		outp=subprocess.Popen("ffmpeg -i \""+s+"\\"+files[i]+"\"", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		info=outp.stdout.read().decode("utf-8")
		if info.find(" Audio: ") < 0:
			continue
		ft.append(ConvertTime(info[info.find("Duration: ")+10:info.find(", ", info.find("Duration: ")+10)]))
		t=FindTime(s, files[i].replace(".flv", ""))
		ft.append(t)
		times.append(t)
		FirstTurn.append(ft)
	times.sort(reverse=False)
	global introsilence
	introsilence = times[0]
	FirstTurn=Sort2D(FirstTurn, 3, False)
	for i in range(len(FirstTurn)):
		FirstTurn[i][3]=FirstTurn[i][3]-times[0]
		FirstTurn[i][0]=i

def FirstAndSecondAnalyzer(f, s):
	while True:
		f=Sort2D(f, 3, False)
		for i in range(len(f)):
			f[i]=f[i][:4]
			f[i].append(0)
		for i in range(len(f)):
			for j in range(i+1, len(f)):
				if f[i][3]+f[i][2] > f[j][3]:
					f[i][4]+=1
					f[j][4]+=1
		f=Sort2D(f, 4, True)
		if len(f)==0:
			return [f, s]
		if f[0][4]!=0:
			s.append(f[0])
			f.pop(0)
			if len(f)==1:
				s.append(f[0])
				f.pop(0)
		else:
			return [f, s]
	return [f, s]

def MergeFiles(f, s):
	global step
	s=s.replace(programpath, ".")
	for i in range(len(f)):
		#print("running started")
		if i>0:
			sd=f[i][3]-f[i-1][3]-f[i-1][2]
		else:
			sd=f[i][3]+1
		cmd="ffmpeg -y -f lavfi -i anullsrc=r=22050 -t "+str(sd)+"ms \""+s+"\\s"+str(i)+ext+"\""
		outp=subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		while True:
			if outp.poll() is not None:
				frm.pPercent.SetValue(int(100*steps[step]/Total))
				step+=1
				break
			time.sleep(0.1)
	cmd="ffmpeg -y "
	for i in range(len(f)):
		cmd+="-i \""+s+"\\s"+str(i)+ext+"\" -i \""+s+"\\"+f[i][1]+"\" "
	cmd+="-filter_complex \""
	for i in range(len(f)*2):
		cmd+="["+str(i)+":a] "
	cmd+="concat=n="+str(len(f)*2)+":v=0:a=1 [a]\" -map \"[a]\" \""+s+"\\m"+f[0][1].replace(".flv", "")+ext+"\""
	#print("merging process has started")
	#print(cmd)
	outp=subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	l1=outp.stdout.readline()
	while True:
		l1=outp.stdout.readline().decode("utf-8")
		if outp.poll() is not None:
			frm.pPercent.SetValue(int(100*steps[step]/Total))
			step+=1
			break
		time.sleep(0.1)
	res=[0]
	res.append("m"+f[0][1].replace(".flv", "")+ext+"")
	res.append(f[len(f)-1][3]+f[len(f)-1][2]-f[0][3])
	res.append(0)
	#print("finished")
	return res

class myframe(wx.Frame):
	def __init__(self, parent):
		wx.Frame.__init__(self, parent)
		self.SetTitle("تبدیل فایلهای کلاس مجازی")
		self.pnl=wx.Panel(self)
		self.lURL=wx.StaticText(self.pnl, label="لینک جلسه")
		self.tURL=wx.TextCtrl(self.pnl)
		self.lName=wx.StaticText(self.pnl, label="نام فایل خروجی")
		self.tName=wx.TextCtrl(self.pnl)
		self.lConvertLink=wx.StaticText(self.pnl, label="دریافت لینک دانلود")
		self.bConvertLink=wx.Button(self.pnl, label="دریافت لینک دانلود")
		self.bConvertLink.Bind(wx.EVT_BUTTON, self.ConvertLink)
		self.lConvertFiles=wx.StaticText(self.pnl, label="تبدیل به mp3")
		self.bConvertFiles=wx.Button(self.pnl, label="تبدیل به mp3")
		self.bConvertFiles.Bind(wx.EVT_BUTTON, self.ConvertFiles)
		self.lStatus=wx.StaticText(self.pnl, label="وضعیت")
		self.tStatus=wx.TextCtrl(self.pnl, size=(500, -1), style=wx.TE_READONLY|wx.TE_MULTILINE)
		self.pPercent=wx.Gauge(self, range=100)
	def ConvertLink(self, e):
		if self.tName.GetValue()=="":
			self.m1=wx.MessageDialog(self, "نام فایل خروجی را وارد کنید", caption="خطا")
			self.m1.ShowModal()
			return
		url=self.tURL.GetValue()
		url2=url.replace("http://", "")
		url2=url2.replace("https://", "")
		uparts=url2.split("/")
		if len(uparts) !=3:
			self.m2=wx.MessageDialog(self, "لینک معتبر نیست", caption="خطا")
			self.m2.ShowModal()
			return
		url=uparts[0]+"/"+uparts[1]+"/output/"+self.tName.GetValue()+".zip?download=zip"
		if not "http" in url:
			url="http://"+url
		self.cb=wx.Clipboard()
		self.cb.Open()
		self.cb.SetData(wx.TextDataObject(url))
	def ConvertFiles(self, e):
		global IsRunning
		if IsRunning == False:
			IsRunning=True
			UnzipArchives()
			if len(sessions) > 0:
				global t
				t=threading.Thread(target=FileConvert, args=(sessions,))
				t.daemon=True
				t.start()
			else:
				self.mNoFile=wx.MessageDialog(self, "فایلی برای تبدیل پیدا نشد", caption="خطا")
				self.mNoFile.ShowModal()
				IsRunning=False
		else:
			self.mRunning=wx.MessageDialog(self, "عملیات تبدیل در حال انجام است", caption="خطا")
			self.mRunning.ShowModal()

def vFileConvert(vFirstTurn, vSecondTurn):
	global steps
	global Total
	steps=[]
	Total=0
	if True:
		while len(vFirstTurn)+len(vSecondTurn)>1:
			r=vFirstAndSecondAnalyzer(vFirstTurn, vSecondTurn)
			vFirstTurn=r[0]
			vSecondTurn=r[1]
			if len(vFirstTurn)==0:
				tvSecondTurn=[]
				rst=[]
				for i in range(len(vSecondTurn)):
					if vSecondTurn[i][3] > 0:
						Total+=vSecondTurn[i][3]
						steps.append(Total)
						Total+=2*(vSecondTurn[i][3]+vSecondTurn[i][2])
						steps.append(Total)
						res=[0]
						res.append("m"+vSecondTurn[i][1].replace(".flv", "")+ext+"")
						res.append(vSecondTurn[i][2]+vSecondTurn[i][3])
						res.append(0)
						rst.append(i)
						tvSecondTurn.append(res)
				vSecondTurn+=tvSecondTurn
				for i in range(len(rst)-1, -1, -1):
					vSecondTurn.pop(rst[i])
				break
			vSecondTurn.append(vMergeFiles(vFirstTurn))
			vFirstTurn=[]
			r=vFirstAndSecondAnalyzer(vSecondTurn, vFirstTurn)
			vSecondTurn=r[0]
			vFirstTurn=r[1]
			if len(vSecondTurn)==0:
				tvFirstTurn=[]
				rst=[]
				for i in range(len(vFirstTurn)):
					if vFirstTurn[i][3] > 0:
						Total+=vFirstTurn[i][3]
						steps.append(Total)
						Total+=2*(vFirstTurn[i][3]+vFirstTurn[i][2])
						steps.append(Total)
						res=[0]
						res.append("m"+vFirstTurn[i][1].replace(".flv", "")+ext+"")
						res.append(vFirstTurn[i][2]+vFirstTurn[i][3])
						res.append(0)
						rst.append(i)
						tvFirstTurn.append(res)
				vFirstTurn+=tvFirstTurn
				for i in range(len(rst)-1, -1, -1):
					vFirstTurn.pop(rst[i])
				break
			vFirstTurn.append(vMergeFiles(vSecondTurn))
			vSecondTurn=[]
		if len(vFirstTurn)>0:
			inp=vFirstTurn
		else:
			inp=vSecondTurn
		max=0
		for i in range(len(inp)):
			if inp[i][2] > max:
				max=inp[i][2]
		Total+=2*max
		steps.append(Total)

def vSort2D(l, i, r=True):
	a=[]
	res=[]
	for s in l:
		a.append(s[i])
	oi=a[:]
	a.sort(reverse=r)
	for b in a:
		f=oi.index(b)
		res.append(l[f])
		l.pop(f)
		oi.pop(f)
	return res

def vFirstAndSecondAnalyzer(f, s):
	while True:
		f=vSort2D(f, 3, False)
		for i in range(len(f)):
			f[i]=f[i][:4]
			f[i].append(0)
		for i in range(len(f)):
			for j in range(i+1, len(f)):
				if f[i][3]+f[i][2] > f[j][3]:
					f[i][4]+=1
					f[j][4]+=1
		f=vSort2D(f, 4, True)
		if len(f)==0:
			return [f, s]
		if f[0][4]!=0:
			s.append(f[0])
			f.pop(0)
			if len(f)==1:
				s.append(f[0])
				f.pop(0)
		else:
			return [f, s]
	return [f, s]

def vMergeFiles(f):
	global Total
	global steps
	sds=[]
	for i in range(len(f)):
		if i>0:
			sd=f[i][3]-f[i-1][3]-f[i-1][2]
		else:
			sd=f[i][3]+1
		Total+=sd
		steps.append(Total)
		sds.append(sd)
	sum=0
	for i in range(len(f)):
		sum+=sds[i]+f[i][2]
	Total+=2*sum
	steps.append(Total)
	res=[0]
	res.append("m"+f[0][1].replace(".flv", "")+ext+"")
	res.append(f[len(f)-1][3]+f[len(f)-1][2]-f[0][3])
	res.append(0)
	return res

def SetConfiguration():
	global ext
	global OutExt
	global DAC
	try:
		f=open("config.ini", "r")
	except OSError:
		SetDefaultConfiguration()
		f=open("config.ini", "r")
	configs=f.read()
	f.close()
	conf=configs.split("\n")
	if len(conf)<3:
		SetDefaultConfiguration()
		return
	c1=conf[0].split(":")
	if len(c1)!=2:
		SetDefaultConfiguration()
		return
	if c1[1] == "no":
		ext=".ogg"
	else:
		ext=".wav"
	c2=conf[1].split(":")
	if len(c2)!=2:
		SetDefaultConfiguration()
		return
	OutExt=c2[1]
	c3=conf[2].split(":")
	if len(c3)!=2:
		SetDefaultConfiguration()
		return
	if c3[1] == "no":
		DAC=False
	else:
		DAC=True

def SetDefaultConfiguration():
	f=open("config.ini", "w")
	DefaultConf="Use wave format:yes\nOutput format:mp3\nDelete zip files after conversion:yes"
	f.write(DefaultConf)
	f.close()

app=wx.App()
frm=myframe(None)
frm.Show()
app.MainLoop()