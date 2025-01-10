from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from .forms import DocumentForm
from .models import Document, FileUpload
import pandas as pd
from . import Analysis
import numpy as np
import scipy.stats as sc
import os, tempfile, base64, requests, io, json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger  # Import EmptyPage and PageNotAnInteger




# Create your views here.
def upload(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save()
            try: 
                 ##### For procession ####

                 with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                     df = pd.read_csv(document.file.path)
                     df.to_pickle(temp_file.name)
                     temp_filepath = temp_file.name
                 
                 with open(temp_filepath, 'rb') as tf:
                      pickled_data = tf.read()
                 
                  # Encode the pickled data to base64
                 encoded_df = base64.b64encode(pickled_data).decode('utf-8')  # Encode and decode to string
                 request.session['uploaded_df'] = encoded_df # Store the base64 encoded string
                 
                 os.remove(temp_filepath)
                 os.remove(document.file.path)
                 
                 
                
            
            except Exception as e:
                 print(f"Error processing or deleting file: {e}")
                 document.delete()  # Cleanup if there's an error
                 return render(request, 'upload_error.html', {'error': str(e)}) # Make an error page!
            return redirect('upload:file_list')
        
    else:
            form = DocumentForm()
    return render(request, 'upload.html', {'form':form})



def file_list(request):
     encoded_df = request.session.get('uploaded_df')
     try:
        pickled_data = base64.b64decode(encoded_df) # Decode from base64 string to bytes
        with tempfile.NamedTemporaryFile(delete=False, mode='wb') as temp_file:
            temp_file.write(pickled_data)  # Write bytes to temp file
            temp_file_path = temp_file.name

        df = pd.read_pickle(temp_file_path)
        os.remove(temp_file_path)

            # ... operations with the dataframe
        context = {'df': df}

        query = request.GET.get('q', '')  # Get query, default to empty string
        column = request.GET.get('column', '')  # Get column, default to empty

        if query:
            if column: # Search specific column
                filtered_df = df[df[column].astype(str).str.contains(query, case=False, na=False)]
            else: # Search all columns
                filtered_df = df[df.apply(lambda row: row.astype(str).str.contains(query, case=False, na=False).any(), axis=1)]
        else:
            filtered_df = df  # Show all data if no search query

        paginator = Paginator(filtered_df, 50) # Create a Paginator object with 50 items per page
        page_number = request.GET.get('page') # Get the current page number from the request
            
        
        try:  # Handle invalid page numbers gracefully
            page_obj = paginator.get_page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.get_page(1)  # Default to first page
        except EmptyPage:
            page_obj = paginator.get_page(paginator.num_pages) # Default to last page if too high
             
        context['page_obj'] = page_obj
        context['query'] = query
        context['selected_column'] = column
        return render(request, 'file_list.html', context)

     except Exception as e:
         error_message = f"An unexpected error occurred: {str(e)}" #General Error Page
         return render(request, 'upload/upload_error.html', {'error': error_message}) 


def report(request):
   
    
    df = request.session.get('uploaded_df')
    if df is None:
        return render(request, 'upload/file_list.html')

    context = {}
    pickled_data = base64.b64decode(df)
    df = pd.read_pickle(io.BytesIO(pickled_data))

    if not isinstance(df, pd.DataFrame) or df.empty: # Handle empty or invalid DataFrames
        return render(request, 'report.html', {'error': 'No data available or invalid DataFrame. Please upload a valid file.'}) # Explain the error

    analysis = Analysis.Analysis(df)
    try:
        # ... (process df)
        report_results = analysis.generate_report() # Get results, a list of lists of dictionaries

        for item in report_results:
            if item and item.get('plot_json'):
                item['plot_json'] = json.dumps(item.get('plot_json'), default=str)  
                print(item['plot_json'])          

        context['report_results'] = report_results
        return render(request, 'report.html', context)  # Return render at the *end* of the function.


    except Exception as e:
        error_message = f"An error occurred during report generation: {str(e)}"
        print(error_message)
        return render(request, 'report.html', {'error': error_message, 'df': df})  # Return render in except block too.


        





def compare(request):
    df = request.session.get('uploaded_df')  # Get DataFrame from session
    pickled_data = base64.b64decode(df)
    df = pd.read_pickle(io.BytesIO(pickled_data)) 
    col1 = None
    col2 = None
    error = None
    context = {'df':df, 'col1':col1, 'col2':col2, 'error':error}
    if request.method == 'POST': # Check if data is in session
        x = request.POST.get('col1')
        y = request.POST.get('col2')
        results = Analysis.Analysis(df).detect_test(df[x], df[y])
        context['results'] = results
    
    return render(request, 'compare.html', context)  # Return render at the *end* of the function.


    


"""


def compare(request):
    df = request.session.get('uploaded_df')  # Initialize outside try-except to ensure it's in scope for the render calls
    col1 = None # Also initialize to None.
    col2 = None
    error = None

    if df is None:
        return render(request, 'compare.html', {'error': 'No data available. Please upload a file.'})
    try: # Make sure we're always working with a valid DataFrame
        pickled_data = base64.b64decode(df)
        df = pd.read_pickle(io.BytesIO(pickled_data))


    except Exception as e:
            print(f"Error processing or deleting file: {e}")
            return render(request, 'upload_error.html', {'error': str(e)}) # Make an error page!

    if request.method == 'POST':
        try:
            
            col1 = request.POST.get('col1')
            col2 = request.POST.get('col2')
            
            if col1 == col2:  # Check if same column selected twice
               raise ValueError("Cannot compare a column with itself") 

            if col1 not in df.columns or col2 not in df.columns:  # Check if both columns exist
                raise ValueError("Invalid column name(s)")
            analysis = Analysis.Analysis(df).detect_test(df[col1], df[col2])

            # ... (Your comparison logic if applicable) ...
            context = {'df': df, 'col1': col1, 'col2': col2, 'error': error, 'analysis':analysis} # Include `error` in context.
            return render(request, 'compare.html', context) #<-- This return was missing!



        except ValueError as ve: #Catch errors like duplicate column selection.

           error=f"Error: {ve}" 
        except KeyError as ke:
            error = f"Key Error: {ke}. Please make sure you have chosen valid columns."
        except Exception as e: # Catch and handle any other exceptions
            error = f"An unexpected error occurred during comparison: {str(e)}" 
        

    context = {'df': df, 'col1': col1, 'col2': col2, 'error': error} # Set context outside of post logic for default template variables.
    return render(request, 'compare.html', context)  # For GET requests or after POST processing.
"""

