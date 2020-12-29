#!/usr/bin/env python3
import os
import csv
from collections import namedtuple
from tkinter import ttk
import tkinter as tk
import tkinter.filedialog as tkfiledialog
import tkinter.messagebox as tkmessagebox
#from tkinter import *
#from tkinter.ttk import *
from guiCorr import *
from prepare import produce_encounter_properties, produce_patient_properties
from prepare import produce_unpivot_files, produce_run_sh_script

DIR_PATH = os.path.dirname(os.path.abspath(__file__))

UnpivotCsv = namedtuple('UnpivotCsv', ['name', 'headers', 'selected', 'unpivoted'])

class Application(tk.Frame):

    def __init__(self, master=None):
        super().__init__(master)
        self.corrs = []
        self.loadTrFunctions()
        self.create_all_frames()
        #self.unpivotcsvs = {}
        self.selected_csv_name = None
        self.outputfolder = None
        self.cde_file = None

    def create_all_frames(self):
        self.hospital_frame()
        self.cdes_metadata_frame()
        self.csv_file_frame()
        self.output_frame()

    def csv_file_frame(self):
        self.harm_labelframe = tk.LabelFrame(self.master, text='CSV File Configuration')
        self.harm_label_csv = tk.Label(self.harm_labelframe, text='CSV File')
        self.csv_file_entry = tk.Entry(self.harm_labelframe)
        #packing
        self.harm_labelframe.grid(row=2, columnspan=8, 
                               padx=4, pady=4, ipadx=4, ipady=4,
                               sticky=['w','e'])
        self.harm_label_csv.grid(row=0, column=0)
        self.csv_file_entry.grid(row=1, column=0)
        #now here comes the repeatable section with the correspondences
        for c in self.corrs:
            self.corr_line(c)
        self.corr_line()
        
    def corr_line(self, c=None):
        if c is None:#all parameters in python are passed by reference
            self.newCButton = tk.Button(self.cde_labelframe, text="New",
                                        command=lambda: guiCorr(self.newCButton,
                                                                c=self.corrs, 
                                                                i=len(self.corrs)+1,
                                                                trFunctions=self.trFunctions))
            self.newCButton.grid(row=len(self.corrs)+1, column=5)
            return
        self.label_corr = tk.Label(self.labelframe, text="Mapping #"+self.corrs.index(c)+"# to "+c.target)
        self.editCButton = tk.Button(self.labelframe, text="Edit")
        #packing
        self.label_corr.grid(row=i+1, column=0)
        self.editCButton.grid(row=i+1, column=5)

    def hospital_frame(self):
        self.hosp_labelframe = tk.LabelFrame(self.master, text='Hospital')
        self.hospital_label = tk.Label(self.hosp_labelframe, text='Hospital Code:')
        self.hospital_entry = tk.Entry(self.hosp_labelframe)
        #packing...
        self.hosp_labelframe.grid(row=0, column=0)
        self.hospital_label.grid(row=0, column=0,sticky='w')
        self.hospital_entry.grid(row=0, column=1, columnspan=2, sticky='w')

    def cdes_metadata_frame(self):
        self.cde_labelframe = tk.LabelFrame(self.master, text='CDEs')
        self.cde_label_file = tk.Label(self.cde_labelframe, text='Metadata file:')
        self.cde_label = tk.Label(self.cde_labelframe, text='Not Selected', bg='white',  width=50)
        self.cde_load_btn = tk.Button(self.cde_labelframe, text='Select', command=self.load_cdes)
        #packing...
        self.cde_labelframe.grid(row=1, column=0)
        self.cde_label_file.grid(row=0, column=0)
        self.cde_label.grid(row=0, column=1, columnspan=3, padx=4, pady=4)
        self.cde_load_btn.grid(row=0, column=5)

    
    def output_frame(self):
        self.out_labelframe = tk.LabelFrame(self.master, text='Output folder')
        self.out_label = tk.Label(self.out_labelframe, text='Not Selected', bg='white', width=50)       
        self.o_button1 = tk.Button(self.out_labelframe, text='Open', command=self.select_output)
        self.o_button2 = tk.Button(self.out_labelframe, text='Create files', command=self.createfiles)
        #packing...
        self.out_labelframe.grid(row=7, column=0)
        self.out_label.grid(row=7, column=1, pady=2)
        self.o_button1.grid(row=7, column=2)
        self.o_button2.grid(row=7, column=3, pady=2, padx=2)

    def loadTrFunctions(self):
        #read the trFunctions.csv and load the trFunctions dict
        #This dict will be loaded in Combobox functions_cbox in guiCorr!!
        self.trFunctions = {}
        with open('trFunctions.csv', 'r') as F:
            functionsFile = csv.DictReader(F)
            for row in functionsFile:
                self.trFunctions[row["label"]]=row["expression"]

    def add_items(self, headers, listbox):
        index = 1
        for header in headers:
            listbox.insert(index, header)
            index += 1

    def load_patient_csv(self):
        filepath = tkfiledialog.askopenfilename(title='select patient csv file',
                                                filetypes=(('csv files', '*.csv'),
                                                           ('all files', '*.*')))
        if filepath:
            csv_name = os.path.basename(filepath)
            self.patientcsv = csv_name
            with open(filepath, 'r') as csvfile:
                data = csv.DictReader(csvfile)
                self.p_csv_label2.config(text=csv_name)
                self.p_csv_headers_cbox.config(values=data.fieldnames)

    def load_visit_csv(self):
        filepath = tkfiledialog.askopenfilename(title='select visits csv file',
                                                filetypes=(('csv files', '*.csv'),
                                                           ('all files', '*.*')))
        if filepath:
            csv_name = os.path.basename(filepath)
            self.visitscsv = csv_name
            with open(filepath, 'r') as csvfile:
                data = csv.DictReader(csvfile)
                self.c_csv_label2.config(text=csv_name)
                self.c_csv_headers_cbox1.config(values=data.fieldnames)
                self.c_csv_headers_cbox2.config(values=data.fieldnames)

    def load_unpivot_csv(self):
        filepath = tkfiledialog.askopenfilename(title='select visits csv file',
                                                filetypes=(('csv files', '*.csv'),
                                                           ('all files', '*.*')))
        if filepath:
            csv_name = os.path.basename(filepath)
            with open(filepath, 'r') as csvfile:
                data = csv.DictReader(csvfile)
                unpivot_csv = UnpivotCsv(name=csv_name, headers=data.fieldnames,
                                         selected=set(), unpivoted=set())
                if csv_name not in self.unpivotcsvs:
                    self.u_listbox1.insert(tk.END, csv_name)
                self.unpivotcsvs[csv_name] = unpivot_csv
            self.u_listbox2.delete(0, tk.END)
            self.u_listbox3.delete(0, tk.END)

    def load_cdes(self):
        return
    
    def unload_unpivot_csv(self):
        sel_index = self.u_listbox1.curselection()
        csv_name = self.u_listbox1.get(sel_index)
        del self.unpivotcsvs[csv_name]
        self.u_listbox1.delete(sel_index)
        self.u_listbox2.delete(0, tk.END)
        self.u_listbox3.delete(0, tk.END)
        self.selected_csv_name = None


                    
    def on_select_csv(self, event):
        sel_index = self.u_listbox1.curselection()
        csv_name = self.u_listbox1.get(sel_index)
        csv_item = self.unpivotcsvs[csv_name]
        self.u_listbox2.delete(0, tk.END)
        self.u_listbox3.delete(0, tk.END)
        self.add_items(csv_item.headers, self.u_listbox2)
        self.add_items(csv_item.selected, self.u_listbox3)
        self.selected_csv_name = csv_name
        #self.u_listbox2.insert(tk.END, csv_name)
    
    
    def add_column(self):
        # get selected csv from previous listbox selection <--Update: needs to change
        csv_name = self.selected_csv_name
  
        csv_item = self.unpivotcsvs[csv_name]
        sel_index2 = self.u_listbox2.curselection()
        column = self.u_listbox2.get(sel_index2)
        if column not in csv_item.selected:
            csv_item.selected.add(column)
            csv_item = csv_item._replace(unpivoted = set(csv_item.headers) - csv_item.selected)
            self.u_listbox3.insert(tk.END, column)
            self.unpivotcsvs[csv_name]=csv_item

    def add_function(self):
        ok=True

    def remove_column(self):
        # get selected csv from previous listbox selection
        csv_name = self.selected_csv_name
        csv_item = self.unpivotcsvs[csv_name]
        
        sel_index = self.u_listbox3.curselection()
        column = self.u_listbox3.get(sel_index)
        csv_item.selected.remove(column)
        self.u_listbox3.delete(sel_index)
        csv_item = csv_item._replace(unpivoted = set(csv_item.headers) - csv_item.selected)
        self.unpivotcsvs[csv_name]=csv_item

    def select_output(self):
        outputfolder = tkfiledialog.askdirectory(title='Select Output Folder')
        if outputfolder:
            if not os.path.isdir(outputfolder):
                os.mkdir(outputfolder)
            self.outputfolder = outputfolder
            self.o_label2.config(text=outputfolder)

    def createfiles(self):
        hospital_code = self.hospital_entry.get()
        warningtitle='Could not create config files'

        p_patientid = self.p_csv_headers_cbox.get()

        visitid = self.c_csv_headers_cbox1.get()
        c_patienid = self.c_csv_headers_cbox2.get()

        if hospital_code == '':
            tkmessagebox.showwarning(warningtitle,
                                     'Please, enter hospital code')
        
        elif not self.patientcsv:
            tkmessagebox.showwarning(warningtitle,
                                     'Please, select patient csv file')

        elif not p_patientid:
            tkmessagebox.showwarning(warningtitle,
                                     'Please, select patientID column in patient csv')

        elif not self.visitscsv:
            tkmessagebox.showwarning(warningtitle,
                                     'Please, select visits csv file')

        elif not visitid:
            tkmessagebox.showwarning(warningtitle,
                                     'Please, select visitID column in visits csv')

        elif not c_patienid:
            tkmessagebox.showwarning(warningtitle,
                                     'Please, select patientID column in visits csv')

        elif not self.outputfolder:
            tkmessagebox.showwarning(warningtitle,
                                     'Please, select configuration files output folder')

        produce_patient_properties(self.outputfolder, self.patientcsv, p_patientid, hospital_code)
        produce_encounter_properties(self.outputfolder, self.visitscsv, visitid, c_patienid, hospital_code)
        produce_run_sh_script(self.outputfolder, self.unpivotcsvs)
        if len(self.unpivotcsvs) != 0:
            for key, item in self.unpivotcsvs.items():
                produce_unpivot_files(self.outputfolder, item.name, item.selected, item.unpivoted)

        tkmessagebox.showinfo(title='Status info',
                message='Config files have been created successully')

        
        
def main(): #(Outside class Application)
    """Main Application Window"""
    root = tk.Tk()
    app = Application(master=root)
    app.master.title('MIPMAP Mappings Configuration')
    app.master.resizable(False, False)
    #app.master.iconbitmap(os.getcwd() + '/images/mipmap.xbm')#needs .ico (or xbm?) file
    app.mainloop()


if __name__ == '__main__':
    main()
 