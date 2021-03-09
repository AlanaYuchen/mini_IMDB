#!/usr/bin/python3
# Author: Team Fake Lovers
# -*- coding: utf-8 -*-
import pandas as pd
from getpass import getpass

# import the psycopg2 database adapter for PostgreSQL
from psycopg2 import connect, sql

# for the sys.exit() method call
import sys

# import the Pygame libraries
import pygame
from pygame.locals import *

# set the DB name, table, and table data to 'None'
db_name = input("Database name: \n")
movie_name = None
movie_buttons = []
title_found = False

# initialize the output with None
movie_list = None
primaryName=None
startYear=None
endYear=None
filmname_return = None
adjusted_rating_return = pd.DataFrame({})

#setting for postgreSQL
#change these globals (user name and user password) to match your settings
user_name = "postgres"
user_pass = getpass("Password: \n")

# create a class for the buttons and labels
class Button():

    # empty list for button registry
    registry = []

    # selected button (will have outline rect)
    selected = None

    # pygame RGBA colors
    white = (255, 255, 255, 255)
    dark_blue = (52,73,85, 255)
    dark_blue2 = (121,135,144,255)
    orange = (249,170,51, 255)
    red = (255, 0, 0, 255)
    orange2 = (255,183,77,255)
    orange3 = (255,224,178,255)
    khaki = (240,230,140)

    # default font color for buttons/labels is dark_blue
    def __init__(self, name, loc, color=dark_blue):

        # add button to registry
        self.registry.append(self)

        # paramater attributes
        self.name = name
        self.loc = loc
        self.color = color

        # text attr for button
        self.text = ""

        # size of button changes depending on length of text
        self.size = (int(len(self.text)*200), 200)

        # font.render(text, antialias, color, background=None) -> Surface
        self.font = font.render (
            self.name + " " + self.text, # display text
            True, # antialias on
            self.color, # font color
            self.orange # background color
        )

        # rect for button
        self.rect = self.font.get_rect() # return the Rect instance containing the width and heigth of text boundary
        self.rect.x = loc[0]
        self.rect.y = loc[1]

# function that returns film names that the queried member is involved
def return_film_name (conn):
    
    SQLquery='SELECT title_basics.primaryTitle FROM title_basics \
            INNER JOIN title_principals ON title_principals.tconst=title_basics.tconst \
            INNER JOIN name_basics \
            ON title_principals.nconst=name_basics.nconst \
            WHERE (startYear >'+ startYear + 'OR startYear is NULL) AND (endYear <'+ endYear +'OR endYear is NULL) AND name_basics.primaryName=\'' + str(primaryName)+'\';'
    
    print(SQLquery)
    cursor = conn.cursor()
    sql_object=sql.SQL(
            SQLquery
            )
    try:
        cursor.execute( sql_object )
        filmname_return = cursor.fetchall()

        cursor.close()
    except Exception as err:
        print ("PostgreSQL psycopg2 cursor.execute() ERROR:", err)
        filmname_return = None

    return filmname_return    

# function that connects to Postgres
def connect_postgres(db):

    # connect to PostgreSQL
    print ("\nconnecting to PostgreSQL")
    try:
        conn = connect (
            dbname = db, #name of the database
            user = user_name, # username: postgre
            host = "localhost", #localhost with port: 5432
            password = user_pass
        )
    except Exception as err:
        print ("PostgreSQL Connect() ERROR:", err)
        conn = None

    # return the connection object
    return conn

# function that returns movie with queried name
def return_movie_list(conn):
    
    if movie_name== None or movie_name== '':
        return None
    
    SQLquery='SELECT tconst, startyear, primarytitle, genres FROM title_basics WHERE primarytitle=\''+str(movie_name)+'\' AND titletype=\'movie\' ORDER BY startyear;'
    
    print(SQLquery)
        # instantiate a new cursor object
    cursor = conn.cursor()
        # (use sql.SQL() to prevent SQL injection attack)
    sql_object = sql.SQL(
                # pass SQL statement to sql.SQL() method, see http://initd.org/psycopg/docs/sql.html
            SQLquery
        )
    
    try:
        # use the execute() method to put table data into cursor obj
        cursor.execute(sql_object)
        # use the fetchall() method to return a list of all the data
        movie_list = cursor.fetchall()
        # close cursor objects to avoid memory leaks
        cursor.close()
        
        if movie_list == []:
            movie_list = None
            
    except Exception as err:
        # print psycopg2 error and set table data to None
        print("PostgreSQL psycopg2 cursor.execute() ERROR:", err)
        movie_list = None
    
    return movie_list
    
# function that return a dataframe containing information of each member's name, previous average rating and category work in the selected movie
def return_adjusted_rating(conn, T_const, year):  
    try:
        # Step1: get titles that member nconst is involved previously released to the queried movie
        SQLquery ='SELECT get_nconst(\''+ T_const + '\');'
        print(SQLquery)
        cursor = conn.cursor()
        sql_object = sql.SQL(SQLquery)
        cursor.execute(sql_object)
        movie_member = cursor.fetchall()
        
        nconst, category = [], []
        for i in range(0, len(movie_member)):
            nconst.append(movie_member[i][0][1:-1].split(',')[0])
            category.append(movie_member[i][0][1:-1].split(',')[1])
        movie_member = pd.DataFrame({"nconst":nconst,"category":category})
        print(movie_member)
        
        #Step2: for each member, get their previous films
        SQLquery = 'SELECT get_tconst_on_nconst_list(ARRAY ' + str(list(movie_member.loc[:, 'nconst'])) + ', ' + str(year) + ');'
        sql_object = sql.SQL(SQLquery)
        cursor.execute(sql_object)
        member_films = cursor.fetchall()
        movie_member['tconst'] = [[] for i in range(movie_member.shape[0])]
        for i in range(movie_member.shape[0]):
            for j in range(len(member_films)):
                if movie_member.loc[i, 'nconst'] == member_films[j][0].split(',')[1][:-1]:
                    movie_member.loc[i, 'tconst'] += [member_films[j][0].split(',')[0][1:]]
        
        #Step3: get the average rating of titles
        result_ratings = []
        result_names = []
        if not movie_member.empty:
            for i in range(0, movie_member.shape[0]):
                if movie_member.loc[i, 'tconst'] != []:
                    SQLquery = sql.SQL("SELECT previous_ratingave(ARRAY " + str(movie_member.loc[i,'tconst']) + ");")
                    print(SQLquery)
                    cursor.execute(SQLquery)
                    temp = cursor.fetchall()[0][0]
                    if temp != None:
                        result_ratings.append(temp)
                    else:
                        result_ratings.append("No rating record")
                else:
                    result_ratings.append('No movie record')
                
                SQLquery = sql.SQL("SELECT get_name(\'" + movie_member.loc[i, 'nconst'] + "\');")
                print(SQLquery)
                cursor.execute(SQLquery)
                result_names.append(cursor.fetchall()[0][0])
                
            #insert the average rating and the name to the original dataframe
            movie_member["previous_ratingAve"] = result_ratings
            movie_member["name"] = result_names
            
            #Step4: get the original score of queried movie
            SQLquery = sql.SQL('SELECT averagerating FROM title_ratings WHERE tconst = \''+ T_const + '\';')
            print(SQLquery)
            cursor.execute(SQLquery)
            original_rating_return = cursor.fetchall()[0][0]
            if original_rating_return != None:
                movie_member["original rating"] = [(float)(original_rating_return)]*len(movie_member)
            else:
                movie_member["original rating"] = [(original_rating_return)]*len(movie_member)
            
            adjusted_rating_return = movie_member
            
        else:
            adjusted_rating_return = pd.DataFrame({})
                 
        
        cursor.close()
        
    except Exception as err:
        print("PostgreSQL psycopg2 cursor.execute() ERROR:", err)
        adjusted_rating_return = pd.DataFrame({})
    
    return adjusted_rating_return
    

"""
PYGAME STARTS HERE
"""

# initialize the pygame window
pygame.init()
pygame.display.set_mode((1000, 1000))
mode = 0 # switch between two queries; 1: query 1; 2: query 2

# change the caption/title for the Pygame app
pygame.display.set_caption("DST2 SQL Final Project", "DST2 SQL Final Project")

# get the OS screen/monitor resolution
max_width = pygame.display.Info().current_w
max_height = pygame.display.Info().current_h

# create a pygame resizable screen
screen = pygame.display.set_mode(
    (int(max_width*0.55), int(max_height*0.6)),
    HWSURFACE | DOUBLEBUF| RESIZABLE
)

# calculate an int for the font size
font_size = int(max_width / 50)

try:
    font = pygame.font.SysFont('Calibri', font_size)
except Exception as err:
    print ("pygame.font ERROR:", err)
    font = pygame.font.SysFont('Arial', font_size)

# create  for PostgreSQL database and table (name, location, color)
query1_button = Button("[Query 1]: Adjusted movie rating according to title", (10, 10))
query2_button = Button("[Query 2]: Search for titles according to crew name and time period", (10, 30))

# default Postgres connection is 'None'
connection = None

# begin the pygame loop
app_running = True
while app_running == True:
    # reset the screen
    screen.fill( Button.orange )
    pygame.draw.rect(screen, Button.dark_blue, (0,240,max_width * 0.55, 35), 0)
    pygame.draw.rect(screen, Button.dark_blue2, (0,275,max_width * 0.55, max_height * 0.6-200), 0)
    if mode != 0:
        pygame.draw.rect(screen, Button.dark_blue, (0, max_height * 0.6-30, 90, 30), 0)

    # set the clock FPS for app
    clock = pygame.time.Clock()

    # iterate over the pygame events
    for event in pygame.event.get():

        # user clicks the quit button on app window
        if event.type == QUIT:
            app_running = False
            pygame.display.quit()
            pygame.quit()
            sys.exit()
            quit()

        # user presses a key on keyboard
        if event.type == KEYDOWN:
            if Button.selected != None:
                # get the selected button
                b = Button.selected
                
                # user presses the return key
                if event.key == K_RETURN: #K_RETURN: 回车键
                    
                    movie_list = None
                    adjusted_rating_return = pd.DataFrame({})
                    
                    connection = connect_postgres( db_name )
                    # check if connection is invalid     
                    if connection == None:
                        blit_text = "PostgreSQL connection is invalid."
                        color = Button.red
                        # blit the message to the pygame screen
                        conn_msg = font.render(blit_text, True, Button.red, Button.dark_blue)
                        screen.blit(conn_msg, (10, 245))

                    # check if the selected button is the movie list display
                    if b in movie_buttons:
                        T_const = b.text.split(";")[0][4:]
                        year =  b.text.split(";")[1][7:]
                        # delete all the buttons of movie list
                        del(Button.registry)[2:len(movie_buttons)+2]
    
                        adjusted_rating_return = return_adjusted_rating(connection, T_const, year)
                    
                    # check if the selected button is the movie name
                    if "Movie Title" in b.name:
                        movie_list = return_movie_list( connection )
                
                    
                    # only when all 3 information is given by the user the SQL query will be called
                    if primaryName != None and startYear != None and endYear != None \
                        and primaryName != '' and startYear != '' and endYear != '':
                        filmname_return = return_film_name( connection )
                        print('Film found:',filmname_return)

                    # reset the button selected
                    Button.selected = None
                    
                else:
                        
                    # get the key pressed
                    key_press = pygame.key.get_pressed()

                    # iterate over the keypresses
                    for keys in range(255):
                        if key_press[keys]:
                            if keys == 8: # backspace
                                b.text = b.text[:-1]
                            else:
                                # convert key to unicode string
                                b.text += event.unicode
                                print ("KEYPRESS:", event.unicode)

                # append the button text to button font object
                b.font = font.render(b.name + " " + b.text, True, Button.dark_blue, Button.orange)
                
                if "Primary Name" in b.name:
                    primaryName = b.text
                    
                if "Start Year" in b.name:
                    startYear = b.text
                    
                if "End Year" in b.name:
                    endYear = b.text
                    
                if "Movie Title" in b.name:
                    movie_name = b.text

        # check for mouse button down events
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            print ("\nMOUSE CLICK:", event)

            # iterate over the button registry list
            for b in Button.registry:

                # check if the mouse click collided with button
                if b.rect.collidepoint(event.pos) == 1:
                    # store button object under selected attr
                    Button.selected = b
                    
                    if "Query 1" in b.name:
                        mode = 1
                        Button.registry = []
                        movie_title_button = Button("Movie Title:", (10, 10))
                        exit_button = Button("<<< Restart",(10, max_height * 0.6-20))
                    elif "Query 2" in b.name:
                        mode = 2
                        Button.registry = []
                        primaryName_button = Button("Primary Name:", (10, 10))
                        startYear_button = Button("Start Year:", (10, 30))
                        endYear_button = Button("End Year:", (10, 50))
                        exit_button = Button("<<< Restart",(10, max_height * 0.6-20))
        
                    elif b.name == "<<< Restart":
                        mode = 0
                        # reset all
                        movie_name = None
                        movie_buttons = []
                        title_found = False
                        movie_list = None
                        primaryName=None
                        startYear=None
                        endYear=None
                        connection = None
                        filmname_return = None
                        adjusted_rating_return = pd.DataFrame({})
                        Button.registry.clear()
                        query1_button = Button("[Query 1]: Adjusted movie rating according to title", (10, 10))
                        query2_button = Button("[Query 2]: Search for titles according to crew name and time period", (10, 30))

    # iterate over the button registry list
    for b in Button.registry:
        
        if mode == 0 and ("Query 1" in b.name or "Query 2" in b.name):
            screen.blit(b.font, b.rect)
        
        if mode == 1:
            if b.name != "Primary Name:" and b.name != "Start Year:" and b.name != "End Year:":
                if Button.selected == b:
                    rect_pos = (b.rect.x-10, b.rect.y-5, max_width * 0.55, b.rect.height+10)
                    pygame.draw.rect(screen, b.khaki, rect_pos, 0) # 0: fill the rectangle
                    pygame.draw.rect(screen, (255,200,140), rect_pos, 2)# 2: 1px frame
                    if b in movie_buttons:
                        b.name = " \>" + b.name[3:]
                    b.font = font.render(b.name + " " + b.text, True, b.color, b.khaki)
                else:
                    if b in movie_buttons:
                        b.name = "( )" + b.name[3:]
                    b.font = font.render(b.name + " " + b.text, True, b.color, b.orange)   
                    if b.name == "<<< Restart":
                        b.font = font.render(b.name + " " + b.text, True, b.orange, b.dark_blue)
                    
                screen.blit(b.font, b.rect)
                    
        if mode == 2:
            if b.name == "Primary Name:" or b.name == "Start Year:" or b.name == "End Year:" or b.name == "<<< Restart":
            # check if the button has been clicked by user
                if Button.selected == b:
                    # blit an outline around button if selected
                    rect_pos = (b.rect.x-10, b.rect.y-5, max_width * 0.55, b.rect.height+10)
                    pygame.draw.rect(screen, b.khaki, rect_pos, 0) # 0: fill the rectangle
                    pygame.draw.rect(screen, (255,200,140), rect_pos, 2)# 1: 1px frame
                    b.font = font.render(b.name + " " + b.text, True, b.color, b.khaki)
                else:
                    b.font = font.render(b.name + " " + b.text, True, b.color, b.orange)
                    if b.name == "<<< Restart":
                        b.font = font.render(b.name + " " + b.text, True, b.orange, b.dark_blue)
                
                screen.blit(b.font, b.rect)

                
    # blit the PostgreSQL information using pygame's font.render() method
    if mode == 0:
        
        blit_text = "Press the button to select query type."
        conn_msg = font.render(blit_text, True, Button.orange2, Button.dark_blue)
        screen.blit(conn_msg, (10, 250))
    
    elif mode == 1:
        
        if movie_name == None:
            blit_text = "Query 1: Type a movie name or film rating and press 'Return'."
            conn_msg = font.render(blit_text, True, Button.orange2, Button.dark_blue)
            screen.blit(conn_msg, (10, 250))
        
        elif movie_name != None:
            
            # connection is valid and movie list pops up
            if connection != None and title_found == True:
                blit_text = "Click one the movie you refer to and press 'Return'."
                color = Button.orange2
                # blit the message to the pygame screen
                conn_msg = font.render(blit_text, True, color, Button.dark_blue)
                screen.blit(conn_msg, (10, 250))
                
            # connection is valid, but movie doesn't exist
            elif connection != None and title_found == False:
                blit_text = "The PostgreSQL table does not have the record with this movie name."
                color = Button.red
                # blit the message to the pygame screen
                conn_msg = font.render(blit_text, True, Button.red, Button.dark_blue) # button.orange has nothing to do with button, only color display
                screen.blit(conn_msg, (10, 250))   
                
            # connection is valid and adjusted movie score pops up
            if connection != None and not adjusted_rating_return.empty:
                blit_text = "Average rating of each member invloved in movie: "+ movie_name
                color = Button.orange2
                # blit the message to the pygame screen
                conn_msg = font.render(blit_text, True, color, Button.dark_blue)
                screen.blit(conn_msg, (10, 250))
                
    else:
        
        if primaryName == None or primaryName == '':
            blit_text = "Query 2: Type an actor full name, start year and end year and press 'Return'."
            conn_msg = font.render(blit_text, True, Button.orange2, Button.dark_blue)
            screen.blit(conn_msg, (10, 250))

        elif primaryName != None:
            # some name is typed in
            if startYear == None or startYear == '':
                 blit_text = "Please add the start year."
                 color = Button.orange2
                 conn_msg = font.render(blit_text, True, color, Button.dark_blue)
                 screen.blit(conn_msg, (10, 250))
            
            elif endYear == None or startYear == '':  
                 blit_text = "Please add the end year."
                 color = Button.orange2
                 conn_msg = font.render(blit_text, True, color, Button.dark_blue)
                 screen.blit(conn_msg, (10, 250))
             
            # connection is valid, but actor name doesn't exist    
            elif connection != None and filmname_return == []:
                blit_text = "The PostgreSQL table does not have the record with this crew name."
                color = Button.orange2
                # blit the message to the pygame screen
                conn_msg = font.render(blit_text, True, color, Button.dark_blue)
                screen.blit(conn_msg, (10, 250))
            
            else: 
                blit_text = "Press 'Return' once you are ready."
                color = Button.orange2
                conn_msg = font.render(blit_text, True, color, Button.dark_blue)
                screen.blit(conn_msg, (10, 250))
            
    # enumerate() the actor first name data if PostgreSQL API call successful
    if movie_list != None:
        
        title_found = True
        
        for i in range(0,len(movie_list)):
            if movie_list[i][3] == None and movie_list[i][2] != None:
                movie_list[i] = "ID: " + movie_list[i][0] + "; Year: " + str(movie_list[i][1]) + "; Genres: null"
            elif movie_list[i][2] == None and movie_list[i][3]!= None:
                 movie_list[i] = "ID: " + movie_list[i][0] + "; Year: null" + "; Type: " + movie_list[i][3] + "; Genres: " + "/".join(movie_list[i][3])
            elif movie_list[i][2] == None and movie_list[i][3] == None:
                 movie_list[i] = "ID: " + movie_list[i][0] + "; Year: null" + "; Genres: null"
            else:
                 movie_list[i] = "ID: " + movie_list[i][0] + "; Year: " + str(movie_list[i][1]) + "; Genres: " + "/".join(movie_list[i][3])
      
        # pop up a window for the user to specify the ID
        for i in range(len(movie_list)):
            b = Button("( ) opt " + str(i) + ":", (10, 30 + i * font_size))
            b.text = movie_list[i]
            movie_buttons.append(b)
            
        movie_list = None

        
    # enumerate the list of tuple rows
    if not adjusted_rating_return.empty:
        
        blit_text = "Name | Average previous ratings before the queried movie | ID | Job category" 
        table_font = font.render(blit_text, True, Button.orange3, Button.dark_blue2)
        screen.blit(table_font, (10, 295))
        
        total = 0
        cnt = 0
        for i in range(adjusted_rating_return.shape[0]):
            blit_text = adjusted_rating_return.loc[i,'name'] + " | "  \
            + str(adjusted_rating_return.loc[i,'previous_ratingAve']) + " | " \
            + adjusted_rating_return.loc[i,'nconst'] + " | " \
            + adjusted_rating_return.loc[i,'category']
                
            table_font = font.render(blit_text, True, Button.orange3, Button.dark_blue2)
            screen.blit(table_font, (10, 320 + i * font_size))

            # calculate average rating
            if not "No" in str(adjusted_rating_return.loc[i,'previous_ratingAve']):
                total += adjusted_rating_return.loc[i,'previous_ratingAve']
                cnt += 1             
            
        blit_text = "Average previous ratings of all members involved in the queried movie: " + "%.1f" % (total/cnt)
        table_font = font.render(blit_text, True, Button.orange3, Button.dark_blue2)
        screen.blit(table_font, (10, 310 + (i+2) * font_size))
        
        blit_text = "Original rating of the queried movie: " + str(adjusted_rating_return.loc[i,'original rating'])
        table_font = font.render(blit_text, True, Button.orange3, Button.dark_blue2)
        screen.blit(table_font, (10, 310 + (i+3) * font_size))
        
        exit_button.font = font.render(exit_button.name + " " + exit_button.text, True, Button.orange, Button.dark_blue)
        screen.blit(exit_button.font, exit_button.rect)
        
    if filmname_return != None:
        for num, row in enumerate(filmname_return):
            # blit the table data to Pygame window
            blit_text = str(row[0]).encode("utf-8", "ignore")
            table_font = font.render(blit_text, True, Button.orange3, Button.dark_blue2)
            if num * font_size + 300  < max_height - 460:
                screen.blit(table_font, (10, 310 + num * font_size))
            else:
                screen.blit(table_font, (300, 310 + (num-12) * font_size))
        
        exit_button.font = font.render(exit_button.name + " " + exit_button.text, True, Button.orange, Button.dark_blue)
        screen.blit(exit_button.font, exit_button.rect)


    # set the clock FPS for application
    clock.tick(100)

    # use the flip() method to display text on surface
    pygame.display.flip()
    pygame.display.update()
