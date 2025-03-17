#GitHubに登録するわいな
#メイン機能のファイル　Streamlitとソケット通信のメイン動作はこちらに記載する
import streamlit as st
import socket
import time
import ESCVP_CONNECT as EC
import COMMAND_CONTROL as CC

#import pandas as pd


#タイトル
st.title("VP.netかんたん通信:smile:")
#デザイン
col1, col2 = st.columns([400,400], gap= 'large')

# ユーザーからの入力。左側に表示。
col1.header('NW connect')
ip = col1.text_input('IP address', "", help='Enter IP address of Ptojector')
port = col1.number_input('Port number', value = 3629, help = 'Enter port number')
sw = col1.radio(
    'Setting of ”Command communication”.',
    ['Protected','Compatible'], 
    help='Protected : Use "Web Control Password",　Compatible : Use "Monitor password"'
    )
pw = col1.text_input('Password', value = "", type='password')

st.session_state.bt_c= col1.button('Connect')
# 接続ボタン
if st.session_state.bt_c:
    #コネクト→受信データ格納
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    #ソケット通信作成
    sock.settimeout(10)
    try:
        sock.connect((ip, port))        #ipaddress port設定
    except socket.timeout:
        col1.markdown(''':red[Socket connect timeout] :skull_and_crossbones:''')
        sock.close
        st.stop()

    match sw:
        case 'Protected':
            #チャレンジリクエスト
            send_data1 = EC.makeRequest_v2()
            sock.sendall(send_data1)

            #チャレンジリクエスト確認
            col1.write('Send data: '+send_data1.hex())

            #レスポンス待ち
            try:
                recv_data1 = sock.recv(4096)
            except socket.timeout:
                col1.markdown(''':red[V2 connect request timeout] :skull_and_crossbones:''')
                sock.close
                st.stop()

            #メッセージ確定
            message = EC.analyzeRespons(recv_data1)
            #受信データ確認
            col1.write('Receive data: '+recv_data1.hex())

            #tパスワード解決
            send_data2 = EC.makeHashedData_V2(recv_data1, pw)
            sock.sendall(send_data2)

            #パスワード解決リクエスト確認
            col1.write('Send data: '+send_data1.hex())
            #レスポンス待ち
            try:
                recv_data2 = sock.recv(4096)
            except socket.timeout:
                col1.markdown(''':red[V2 password solution timeout] :skull_and_crossbones:''')
                sock.close
                st.stop()
                        
            #メッセージ確定
            message = EC.analyzeRespons(recv_data2)
            #受信データ確認
            col1.write('Receive data: '+recv_data2.hex())
            col1.markdown(message)

        case 'Compatible':
            #プレーンテキストで通信開始
            send_data = EC.makeData_v1(pw)
            sock.sendall(send_data)

            #レスポンス待ち
            try:
                recv_data = sock.recv(4096)
            except socket.timeout:
                col1.markdown(''':red[V1 connect request timeout] :skull_and_crossbones:''')
                sock.close
                st.stop()

            ##メッセージ確定
            message = EC.analyzeRespons(recv_data)
            #送信データ確認
            col1.write('Send data: '+send_data.hex())
            #受信データ確認
            col1.write('Receive data: '+recv_data.hex())
            col1.markdown(message)
        
        case _:
            st.markdown(''':red[なにしたんや。。。] :confused:''')

    #ソケットを保持してあげる
    st.session_state.fsock = sock

#コマンドデータ通信
col2.header('Command')
input_data = col2.text_input('Command', 'PWR?', help='Enter VP21 command')
sw2 = col2.selectbox(
    'Special modes',
    ['-','Temp', 'Other'], 
    help='-: Send command only one time. Temp : Send "Temp?" command per 1 sec. Other : Send above command per 1 sec.'
    )
min = col2.number_input('Command sending time (min.)', value = 1)

#コマンドデータ送信
st.session_state.bt_s = col2.button('Send')
if st.session_state.bt_s:
    match sw2:
        case '-':
            Pre_send_data = input_data + '\x0d'         #改行を追加
            send_data = Pre_send_data.encode('utf-8')   #エンコードデータ作成
            st.session_state.fsock.sendall(send_data)   #コマンド送信
            #レスポンス待ち
            try:
                command_recv = st.session_state.fsock.recv(4096)
            except socket.timeout:
                col1.markdown(''':red[V1 connect request timeout] :skull_and_crossbones:''')
                st.session_state.fsock.close
                st.stop()
            #レスポンス表示
            text_command_recv = command_recv.decode('utf-8')
            col2.write(text_command_recv)

        case 'Temp':
            chart_th = col2.empty()
            chart_fan = col2.empty()

            #電源ONコマンド送付を通達
            st.toast(":zap: Power on")

            #PWR ON
            st.session_state.fsock.sendall(CC.pwr_on)
            time.sleep(0.5)
            try:
                recv_data_pon = st.session_state.fsock.recv(4096)
            except socket.timeout:
                st.session_state.fsock.close
                st.stop()
            
            #PWR ON待ち
            #time.sleep(20)
           
            #TEMPコードで期待の値(TEMP=)が返ってくるまで送付
            checkTemp =""
            i=0
            while checkTemp != "TEMP":
                time.sleep(10)
                st.session_state.fsock.sendall(CC.temp_str)
                try:
                    recv_data_tc = st.session_state.fsock.recv(4096)
                except socket.timeout:
                    st.session_state.fsock.close
                checkTemp = CC.checkCode(recv_data_tc,flag=1)
                #col2.write(checkTemp)
                i +=1
                if i >5:
                    col2.markdown(''':red[Request timeout] :skull_and_crossbones:''')
                    st.stop()
            
            #準備中の旨通知
            st.toast(":hourglass_flowing_sand: Now preparing...")

            #Tempのモニター対象を取得
            st.session_state.fsock.sendall(CC.temp_str)
            try:
                recv_data_ts = st.session_state.fsock.recv(4096)
            except socket.timeout:
                st.session_state.fsock.close
                st.stop()
            #データフレーム作成
            df_th = CC.getThCode(recv_data_ts)          
            df_fan = CC.getFanCode(recv_data_ts)
            #col2.write(df_th)
            #col2.write(df_fan)

            #recvの中身が期待値(TEMP＝0xhh…)になるまで繰り返し
            checkTemp = df_th.columns[1]
            i=0
            while checkTemp == df_th.columns[1]:
                time.sleep(5)
                st.session_state.fsock.sendall(CC.temp_mntr)
                try:
                    recv_data_tc2 = st.session_state.fsock.recv(4096)
                except socket.timeout:
                    st.session_state.fsock.close
                checkTemp = CC.checkCode(recv_data_tc2,flag=2)
                #col2.write(checkTemp)
                i +=1
                if i >5:
                    col2.markdown(''':red[Request timeout] :skull_and_crossbones:''')
                    st.stop()
            #col2.write(checkTemp)

            #モニター開始通知
            st.toast(":rocket: Start monitoring")
            #１秒間隔でTemp？コマンド
            for i in range(min * 60):
                st.session_state.fsock.sendall(CC.temp_mntr)
                time.sleep(1)
                try:
                    recv_data_tm = st.session_state.fsock.recv(4096)
                except socket.timeout:
                    st.session_state.fsock.close
                    st.stop()
                    break
                
                #データフレーム更新
                df_th = CC.getThData(recv_data_tm, i ,df_th)
                df_fan = CC.getFanData(recv_data_tm, i ,df_fan)

                #Chart更新
                chart_th.line_chart(df_th)
                chart_fan.line_chart(df_fan)

            #データ取得用にデータレームの中身表示
            col2.write(df_th)
            col2.write(df_fan)
        
        case 'Other':
            df_disp = col2.empty()                      #
            Pre_send_data = input_data + '\x0d'         #改行を追加
            send_data = Pre_send_data.encode('utf-8')   #エンコードデータ作成

            st.toast(":rocket: Start to send command")
            df = CC.makeDataFrame()
            for i in range(min*60):
                st.session_state.fsock.sendall(send_data)   #コマンド送信
                time.sleep(1)
                try:
                    command_recv = st.session_state.fsock.recv(4096)
                except socket.timeout:
                    col1.markdown(''':red[V1 connect request timeout] :skull_and_crossbones:''')
                    st.session_state.fsock.close
                    st.stop()

                #データフレーム更新/表の表示
                df = CC.getComData(input_data, command_recv, i, df)
                df_disp.dataframe(df,use_container_width=True)
                
