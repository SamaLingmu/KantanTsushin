#ソケット通信の補助関数/変数を定義
import hashlib

#プレーンテキストでのパスワード解決
def makeData_v1(pw=''):
    send_data = b'\x00'         #送信データ格納変数    
    
    pw_len = len(pw)                        #パスワード文字列長さ　パディング用
    send_data = b'ESC/VP.net'               #10bit ヘッダー
    send_data += b"\x10"                    #V1 指定
    send_data += b"\x03"                    #Connectパケット指定
    send_data += b"\x00\x00"                #予約エリア
    send_data += b"\x00"                    #ステータスコード　リクエストは\x0000
    send_data += b"\x01"                    #Hedder数　1
    send_data += b"\x01"                    #ヘッダー　パスワード
    send_data += b"\x01"                    #ヘッダー属性　プレーンテキスト
    send_data += pw.encode()                #パスワード格納
    send_data += b"\x00" * (16 - pw_len)    #パディング

    return send_data

#V2通信のリクエスト
def makeRequest_v2():
    send_data = b'\x00'         #送信データ格納変数    

    send_data = b'ESC/VP.net'   #10bit ヘッダー
    send_data += b"\x20"        #V2 指定
    send_data += b"\x03"        #Connectパケット指定
    send_data += b"\x00\x00"    #予約エリア
    send_data += b"\x00"    #ステータスコード　リクエストは\x0000
    send_data += b"\x01"        #Hedder数　1
    send_data += b"\x01"        #ヘッダー　パスワード
    send_data += b"\x03"        #ヘッダー属性　チャレンジ
    send_data += b"\x00"*16     #空文字列(チャレンジリクエスト仕様)    
    
    return send_data

#V2のパスワード解決
def makeHashedData_V2(recv_data1=b'\x00', pw=''):
    send_data = b'\x00'         #送信データ格納変数
    #ハッシュ値作成
    nonce =  recv_data1[18:34]
    hash_pw = hashlib.sha256(('ESC/VP.net:' + pw).encode())         #文字列→文字コード→shaハッシュ化

    A = hash_pw.hexdigest()                                         #ハッシュ化16進数コードを文字列として格納
    nonce_hex = nonce.hex()                                          #nonceを16進数の文字コードに変換
    response_hash = hashlib.sha256((A + ":" + nonce_hex).encode())  #文字列→文字コード→shaハッシュ化
    response = response_hash.digest()                               #ハッシュ化16進数コードを格納

    #チャレンジ通信要求
    send_data = b'ESC/VP.net'       #10bit ヘッダー
    send_data += b"\x20"            #V2 指定
    send_data += b"\x03"            #Connectパケット指定
    send_data += b"\x00\x00"        #予約エリア
    send_data += b"\x00"            #ステータスコード　リクエストは\x0000
    send_data += b"\x02"            #Hedder数　2
    send_data += b"\x01"            #ヘッダー　パスワード
    send_data += b"\x04"            #ヘッダー属性　チャレンジレスポンス1
    send_data += response[0:16]     #空文字列(チャレンジリクエスト仕様)
    send_data += b"\x01"            #ヘッダー　パスワード
    send_data += b"\x05"            #ヘッダー属性　チャレンジレスポンス２
    send_data += response[16:32]    #空文字列(チャレンジリクエスト仕様)       

    return send_data

#返答判別/エラーメッセー時
def analyzeRespons(recv_data=b'\x00'):
    message = ''
    result_flag = recv_data[14:15] #エラー処理
    match result_flag:
        case b'\x20':
            message = f''':green[*Connect success*] :white_check_mark:\n :green[おめでと～]'''
        case b'\x41':
            message = f''':red[*No password request is not supported in this App*] :pleading_face:'''
        case b'\x43':
            message = f''':red[*Password is not correct*] :x:'''
        case b'\x45':
            message = f''':red[*Command communication” is not matched*] :underage:'''
        case b'\x53':
            message = f''':red[*Projector is busy*] :hot_face:'''
        case _:
            message = f''':red[*Unknown failure*] :confused:'''

    return message