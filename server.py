#-*- coding:utf-8 -*-
import sys, os, BaseHTTPServer, subprocess

class base_case(object):
    '''条件处理基类'''
    def handler_file(self, handler, full_path):
        try:
            with open(full_path, 'rb') as reader:
                content = reader.read()
            handler.send_content(content)
        except IOError as msg:
            msg = "'{0}' cannot be read: {1}".format(full_path, msg)
            handler.handle_error(msg)

    def index_path(self, handler):
        return os.path.join(handler.full_path, 'index.html')
    # 要求子类必须实现该接口
    def test(self, handler):
        assert False, 'Not implemented.'
    def act(self, handler):
        assert False, 'Not implemented.'

class case_no_file(object):
    '''该路径不存在'''
    def test(self, handler):
        return not os.path.exists(handler.full_path)
    def act(self, handler):
        raise ServerException("'{0}' not found".format(handler.path))

class case_existing_file(object):
    '''该路径是文件'''
    def test(self, handler):
        return os.path.isfile(handler.full_path)
    def act(self, handler):
        handler.handle_file(handler.full_path)

class case_always_fail(object):
    '''所有情况都不符合时的默认处理类'''
    def test(self, handler):
        return True
    def act(self, handler):
        raise ServerException("Unknown object '{0}'".format(handler.path))

class case_directory_index_file(base_case):
    # 判断目标路径是否是目录&&目录下是否有index.html
    def test(self, handler):
        return os.path.isdir(handler.full_path) and os.path.isfile(self.index_path(handler))
    # 响应index.html的内容
    def act(self, handler):
        handler.handler_file(self.index_path(handler))

class case_cgi_file(object):
    '''脚本文件处理'''
    def test(self, handler):
        return os.path.isfile(handler.full_path) and handler.full_path.endswith('.py')
    def act(self, handler):
        # 运行脚本文件
        handler.run_cgi(handler.full_path)

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    '''处理请求并返回页面'''

    # 页面模板
#    Page = '''\
#<html>
#<body>
#<p>Hello, web!</p>
#</body>
#</html>
#    '''

    Page = '''\
<html>
<body>
<table>
<tr>  <td>Header</td>         <td>Value</td>          </tr>
<tr>  <td>Date and time</td>  <td>{date_time}</td>    </tr>
<tr>  <td>Client host</td>    <td>{client_host}</td>  </tr>
<tr>  <td>Client port</td>    <td>{client_port}</td> </tr>
<tr>  <td>Command</td>        <td>{command}</td>      </tr>
<tr>  <td>Path</td>           <td>{path}</td>         </tr>
</table>
</body>
</html>
'''

    # 所有可能的情况
    Cases = [case_no_file(),
             case_cgi_file(),
             case_existing_file(),
             case_directory_index_file(),
             case_always_fail()]

    # 处理一个GET请求
    def do_GET(self):
#        self.send_response(200)
#        self.send_header("Content-Type", "text/html")
#        self.send_header("Content-Length", str(len(self.Page)))
#        self.end_headers()
#        self.wfile.write(self.Page)

#        page = self.create_page()
#        self.send_content(page)

        try:
            # 文件完整路径
            full_path = os.getcwd() + self.path
            # 如果该路径不存在...
#            if not os.path.exists(full_path):
                #抛出异常：文件未找到
#                raise ServerException("'{0}' not found".format(self.path))
            # 如果该路径是一个文件
#            elif os.path.isfile(full_path):
                #调用 handle_file 处理该文件
#                self.handle_file(full_path)
            # 如果该路径不是一个文件
#            else:
                #抛出异常：该路径为不知名对象
#                raise ServerException("Unknown object '{0}'".format(self.path))

            # 遍历所有可能的情况
            for case in self.Cases:
                handler = case()
                # 如果满足该类情况
                if handler.test(self):
                    # 调用相应的act函数
                    handler.act(self)
                    break

        # 处理异常
        except Exception as msg:
            self.handle_error(msg)

    def handle_file(self, full_path):
        try:
            with open(full_path, 'rb') as reader:
                content = reader.read()
            self.send_content(content)
        except IOError as msg:
            msg = "'{0}' cannot be read: {1}".format(self.path, msg)
            self.handle_error(msg)

    Error_Page = """\
<html>
<body>
<h1>Error accessing {path}</h1>
<p>{msg}</p>
</body>
</html>
        """

    def handle_error(self, msg):
        content = self.Error_Page.format(path=self.path, msg=msg)
        self.send_content(content, 404)


    def create_page(self):
        values = {
            'date_time'   : self.date_time_string(),
            'client_host' : self.client_address[0],
            'client_port' : self.client_address[1],
            'command'     : self.command,
            'path'        : self.path
        }
        page = self.Page.format(**values)
        return page

    def send_content(self, content, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def run_cgi(self, full_path):
        data = subprocess.check_output(["python", handler.full_path])
        self.send_content(data)

class ServerException(Exception):
    '''服务器内部错误'''
    pass

#----------------------------------------------------------------------

if __name__ == '__main__':
    serverAddress = ('', 8080)
    server = BaseHTTPServer.HTTPServer(serverAddress, RequestHandler)
    server.serve_forever()