#coding:utf-8
import os, xlrd, xlwt
import sys

cmdb_file = sys.argv[2]
idc_file = sys.argv[1]

def set_style(name,height):
    style = xlwt.XFStyle()

    #设置左对齐
    alignment = xlwt.Alignment()
    alignment.horz = xlwt.Alignment.HORZ_LEFT  # 水平方向
    alignment.vert = xlwt.Alignment.VERT_TOP

    #设置边框
    borders = xlwt.Borders()
    borders.left = xlwt.Borders.THIN
    borders.right = xlwt.Borders.THIN
    borders.top = xlwt.Borders.THIN
    borders.bottom = xlwt.Borders.THIN

    #设置字体
    font = xlwt.Font()
    font.name = name
    font.bold = False
    font.color_index = 4
    font.height = height

    style.font = font
    style.alignment = alignment
    style.borders = borders
    return style

def read_excel():
    wb = xlrd.open_workbook(filename=cmdb_file)
    wp = xlrd.open_workbook(filename=idc_file)
    sheets = wp.sheet_names()
    print(sheets)

    #获取cmdb表里的信息
    sheet_cmdb = wb.sheet_by_index(0)
    col3 = sheet_cmdb.col_values(3)
    col4 = sheet_cmdb.col_values(4)

    #cmdb表里信息合成二维列表，并去重
    tmp = []
    for i in range(1, len(col3)):
        tmp.append([col3[i], str(int(col4[i]))])
    cols = []
    for t in tmp:
        if t not in cols:
            cols.append(t)

    fp = xlwt.Workbook()
    default = set_style('宋体', 220)

    #获取idc表里的相关数据
    for c in range(0, len(sheets)):
        table = wp.sheet_by_name(sheets[c])

        con = table.ncols
        row_s = table.nrows

        #把每个表里的信息放在一个列表上
        n_cols = []
        for i in range(0, con):
            col = table.col_values(i)
            n_cols.append(col)
        emp = ['设备数量']
        for j in range(1, row_s):
            emp.append('0')
        n_cols.append(emp)

        #数据比对
        for val in cols:
            for m in range(1, len(n_cols[0])):
                if n_cols[0][m] in val:
                    n_cols[-1][m] = val[1]

        #print("data_%s = %s" % (c, n_cols))

        #写入新的excel表
        sheet = fp.add_sheet(sheets[c], cell_overwrite_ok=True)
        for e in range(0, len(n_cols)):
            for f in range(0, len(n_cols[e])):
                sheet.write(f, e, n_cols[e][f], default)
                if len(n_cols[e][1]) < 10:
                    sheet.col(e).width = 3333
                else:
                    sheet.col(e).width = 8000

    fp.save('/data/reslut.xls')


read_excel()
