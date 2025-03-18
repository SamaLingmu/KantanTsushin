#コマンド通信の補助関数/変数を定義するファイル
import re
import pandas as pd
import streamlit as st

#変数定義
pwr_off = b'PWR OFF\x0d'
pwr_on = b'PWR ON\x0d'
pwr_cn = b'PWR?\x0d'
temp_str = b'TEMP? 02\x0d'
temp_mntr = b'TEMP?\x0d'

def checkCode(recv_data, flag):
    temp_pram = recv_data.decode('utf-8')       #変換
    pram_list = re.split(r'[ =]', temp_pram)    #区分け   

    if flag == 1: #TEMPになったかの判断の時
        return pram_list[0] #リストの先頭を返す
    if flag ==2:    #データになったかの判断の時
        return pram_list[1] #リストの２つ目を返す


def getThCode(recv_data):
    #受信データからサーミスタのコラムスのみのデータフレームを作る
    temp_pram = recv_data.decode('utf-8')       #変換
    pram_list = re.split(r'[ =]', temp_pram)    #区分け
    temp_header = pram_list.index('TEMP')       #開始の基準としてTEMPの位置
    atmark = pram_list.index('@')               #＠のとこまでの長さ取得
    th_list = pram_list[temp_header+1:atmark]   #THの部分抜き取り
    th_list1 = [f'{th_list[i]}_{i}' if th_list[i]=='XX' else th_list[i] for i in range(len(th_list))]  
    df_th = pd.DataFrame(columns=th_list1)

    return df_th

def getFanCode(recv_data):
    #受信データからfanのコラムスのみのデータフレームを作る
    temp_pram = recv_data.decode('utf-8')       #変換
    pram_list = re.split(r'[ =]', temp_pram)    #区分け
    atmark1 = pram_list.index('@')              #＠のとこまでの長さ取得 
    pram_len = len(pram_list)                   #＠のとこまでの長さ取得 
    fan_list = pram_list[atmark1+1:pram_len-1]  #Fanのところ抜き取り
    fan_list = [f'{fan_list[i]}_{i}' if fan_list[i]=='XX' else fan_list[i] for i in range(len(fan_list))]  

    #データフレーム作成
    df_th = pd.DataFrame(columns=fan_list)

    return df_th

def getThData(recv_data, i , df_th):
    #df_fanに取得したデータをくっつけて返す関数関数
    temp_pram = recv_data.decode('utf-8')                           #変換
    temp_list = re.split(r'[ =]', temp_pram)                        #区分け
    temp_header = temp_list.index('TEMP')
    atmark = temp_list.index('@')                                   #＠のとこまでの長さ取得
    thData_list = temp_list[temp_header+1:atmark]                               #THの部分抜き取り
    thData_list = ['00' if x=='XX' else x for x in thData_list]     #取得不可の部分を00に変換
    thData_list = [int(x, 16)/2 for x in thData_list]               #10進数データに変換

    #データフレーム作成->結合
    df_th2 = pd.DataFrame([thData_list], index =[i], columns=df_th.columns)
    df_concat = pd.concat([df_th, df_th2], axis = 0)

    return df_concat

def getFanData(recv_data, i ,df_fan):
    #df_fanに取得したデータをくっつけて返す関数関数
    temp_pram = recv_data.decode('utf-8')                           #変換
    temp_list = re.split(r'[ =]', temp_pram)                        #区分け
    atmark1 = temp_list.index('@')                                  #＠のとこまでの長さ取得 
    temp_list[atmark1] = 'ATMARK'                                   #@書き換え
    atmark2 = temp_list.index('@')                                  #＠2つ目までの長さ
    fanData_list = temp_list[atmark1+1:atmark2]                     #FANの部分抜き出し

    fanData_list = ['00' if x=='XX' else x for x in fanData_list]   #int型以外の応答を00で変換
    fanData_list = [int(x, 16)/255 for x in fanData_list]           #%表示に変換

    #データフレーム作成->結合
    df_fan2 = pd.DataFrame([fanData_list], index = [i], columns=df_fan.columns)
    df_concat = pd.concat([df_fan, df_fan2],axis = 0)

    return df_concat

def makeDataFrame():
    return pd.DataFrame(columns=['Command', 'Return'])

def getComData(send_data, recv_data, i , df):
    recv_text = recv_data.decode('utf-8')                           #変換
    df2 = pd.DataFrame([[send_data,recv_text]], index=[i], columns=['Command', 'Return'])
    df_concat = pd.concat([df, df2],axis = 0)

    return df_concat