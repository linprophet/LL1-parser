# -*- coding: utf-8 -*-
"""
Created on Sun May 10 09:59:15 2020

@author: prophet lin
"""

import os
import pandas as pd
import numpy as np
out = open("./res.txt", 'w+')

#%% 读取生成式  @表示为空
generator = {}
start = None    #开始符号
ter_set = set() #终结符集合
non_set = set() #非终结符集合
all_set = set()
#grammar2
f = open('./tiny.txt')
for line in f:
    line = line.split('->')
    #添加开始符号
    if not non_set:
        start = line[0].split()[0]
    #非终结符
    non_sym = line[0].split()[0]
    non_set.add(non_sym)
    #右侧所有符号 
    all_syms = line[1].split() #[:-1] delete '/n'
    all_set = all_set.union(set(all_syms))
    
    if non_sym not in generator:
        generator[non_sym] = []
    generator[non_sym].append(all_syms)
#求非终结符集
ter_set = all_set - non_set
print("起始符号：{0}\n非终结符：{1}\n终结符：{2}\n===========".format(start, non_set, ter_set), file=out)
#%% 消除左递归

#%% 提取左因子

#%% 生成First集
first = {}
#第一轮 把所有开头的非终结符和空放入First集
for l_sym in generator:
    for each in generator[l_sym]:
        if l_sym not in first:
            first[l_sym] = set()
        if each[0] in ter_set:
            first[l_sym].add(each[0])
#循环轮 添加非终结符，循环直到不再变化
update = 1
while update == 1:
    update = 0
    for l_sym in generator:
        for each in generator[l_sym]:
            #处理空符号，尤其是前面所有的均为空
            emputy_flag = 0
            for i in range(len(each)):
                if each[i] in non_set:
                    #如果添加导致改变，设置标志位
                    temp = first[l_sym].union( first[each[i]] - set('@') )
                    if first[l_sym] != temp:
                        update = 1
                        first[l_sym] = temp
                if each[i] in ter_set and each[i] not in first[l_sym]:
                    update = 1
                    first[l_sym].add(each[i])
                if each[i] in ter_set or (each[i] in non_set and '@' not in first[each[i]]):
                    emputy_flag = 1
                    break
                
            if emputy_flag == 0:
                first[l_sym].add('@')

print("First集：", file=out)     
for item in first:
    print("{0}:{1}".format(item,first[item]), file=out)   
print("===========", file=out)   
#%% 生成Follow集
# $ 加入起始符号
follow = {}        
for non_sym in non_set:
    follow[non_sym] = set()
follow[start] = set('$')

# 第一轮 将非终结符后的终结符添加到FOLLOW中
for l_sym in generator:
    for each in generator[l_sym]:
        for i in range(len(each)-1):
            if each[i] in non_set and each[i+1] in ter_set:
                follow[each[i]].add(each[i+1])
#第二轮 集合间的同步，非终结符后的非终结符first集，左侧添加到右侧最后，循环直到不再变化
update = 1
while update == 1:
    update = 0
    for l_sym in generator:
        for each in generator[l_sym]:
            # 产生式后加入$,用来合并逻辑,不必从末尾向前找空，而是顺序向后
            temp_produce = each.copy()
            temp_produce.append('$')
            for i in range(len(each)):
                next_p = i
                while True:
                    next_p += 1
                    #非终结符后的非终结符first集
                    if temp_produce[i] in non_set and temp_produce[next_p] in non_set:
                        temp = follow[temp_produce[i]].union( first[temp_produce[next_p]] - set('@') )
                        if follow[temp_produce[i]] != temp:
                            update = 1
                            follow[temp_produce[i]] = temp
                    #左侧follow添加到右侧最后
                    if temp_produce[i] in non_set and temp_produce[next_p] == '$':
                        temp = follow[temp_produce[i]].union( follow[l_sym] )
                        if follow[temp_produce[i]] != temp:
                            update = 1
                            follow[temp_produce[i]] = temp
                    if temp_produce[next_p] in ter_set or temp_produce[next_p] == '$' or ( '@' not in first[temp_produce[next_p]]):
                        break
print("Follow集：", file=out)     
for item in follow:
    print("{0}:{1}".format(item,follow[item]), file=out)   
print("===========", file=out)       
#%% 生成LL1分析表 判断是否是LL1文法
vaild = True
ter_list = list(ter_set)
non_list = list(non_set)
ter_list.append('$')
ter_list.remove('@')
ll1_table = pd.DataFrame(columns = ter_list,index = non_list)
generator_list = []
count = 0
for l_sym in generator:
    for each in generator[l_sym]:
        #print(each,count)
        generator_list.append([l_sym,each])
        if each[0] == '@':
            #添加Follow
            for sym in follow[l_sym]:
                if np.isnan(ll1_table.loc[l_sym,sym]):
                    ll1_table.loc[l_sym,sym] = count
                else:
                    vaild = False
            count += 1
            continue
        if each[0] in ter_set:
            if np.isnan(ll1_table.loc[l_sym,each[0]]):
                ll1_table.loc[l_sym,each[0]] = count
            else:
                vaild = False
        #TODO:处理first中有空的情况
        if each[0] in non_set:
            for sym in first[each[0]]:
                if np.isnan(ll1_table.loc[l_sym,sym]):
                    ll1_table.loc[l_sym,sym] = count
                else:
                    vaild = False
        count += 1
        
if not vaild:
    print('文法不满足LL（1）条件！')
ll1_table.to_excel('LL1.xlsx')
#%% 分析栈分析代码 以及构造抽象语法树
token_file = open('./token_list.txt')
tokens = []
for line in token_file:
    tokens.append(line[:-1])
tokens.append('$')
stack = []
stack.append("$")
stack.append(start)
while stack:
    print('=====================\n','stack:',stack,'\n tokens:',tokens, file=out)
    
    #match
    if stack[-1] in ter_set or (stack[-1] == '$' and tokens[-1] == '$'):
        if stack[-1] == tokens[0]:
            stack.pop()
            tokens.pop(0)
            continue
        else:
            print('不满足文法')
            break
    #action
    if stack[-1] in non_set:
        if np.isnan(ll1_table.loc[stack[-1],tokens[0]]):
            print('不满足文法')
            break
        else:
            use_p = generator_list[ll1_table.loc[stack[-1],tokens[0]]]
            stack.pop()
            temp = use_p[1].copy()
            if temp[0] != '@':
                temp.reverse()
                stack.extend(temp)

#%%
out.close()
'''
update = 1
while update == 1:
    update = 0
    for l_sym in generator:
        #TODO:处理空符号，尤其是前面所有的均为空
        for each in generator[l_sym]:
            if each[0] in non_set:
                #如果添加导致改变，设置标志位
                temp = first[l_sym].union( first[each[0]] - set('@') )
                if first[l_sym] != temp:
                    update = 1
                    first[l_sym] = temp
'''