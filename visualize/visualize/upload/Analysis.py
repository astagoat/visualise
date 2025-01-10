import numpy as np
import pandas as pd
import scipy.stats as sc
import io, base64, matplotlib
from scipy.stats import chi2_contingency
import seaborn as sns
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.colors as mcolors
from io import BytesIO
'''
import json, plotly
import plotly.graph_objects as go  # Import Plotly
import plotly.io as pio
'''        
def plot_to_base64(plt_figure):
    buf = BytesIO()
    plt_figure.savefig(buf, format='png')
    buf.seek(0)
    plot_data = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.clf()  # Clear the plot after saving
    return plot_data
class Analysis:
    def __init__(self, dataframe):
        """
        Initialize the CorrelationAnalysis class with a pandas DataFrame.

        :param dataframe: pandas DataFrame containing the data to analyze.
        """
        self.dataframe = dataframe
    
    
        
    def num_vs_cat(self, x, y):
        results = []
        a = x
        b = y
        if np.issubdtype(x.dtype, np.number):
            x, y = y, x # x is always the categorical

        #Eta Test

        def eta_squared(x,y):
            # x is categorical, y is numeric
            overall_mean = y.mean()
            ssb = sum(
                y.groupby(x).size() * (y.groupby(x).mean() - overall_mean) ** 2
            )
            sst = sum((y - overall_mean) ** 2)
            eta2 = ssb / sst
            return eta2
    
        results = []
        fig, ax = plt.subplots(figsize=(8, 6))  # Use ax for plotting
        sns.boxplot(x=x, y=y, ax=ax)
        sns.violinplot(x=x, y=y, ax=ax)
        plot = plot_to_base64(fig)        
        
        
        results.append({
            'plot': plot,
            'title': 'Plotly Plot',
            'eta': eta_squared(x, y)})

        return results


    def cat_vs_cat(self, x, y):
        contingency_table = pd.crosstab(x, y)

        # Perform Chi-squared test
        chi2, p, dof, expected = chi2_contingency(contingency_table)

        fig, ax = plt.subplots(figsize=(8, 6))  # Use ax for plotting
        sns.boxplot(x=x, y=y, ax=ax)
        sns.violinplot(x=x, y=y, ax=ax)
        plot = plot_to_base64(fig)  # Function to handle saving and encoding

        


        return [{
            'col1': x.name,
            'col2': y.name,
            'chi2': chi2,
            'p': p,
            'plot': plot
        }]
    

    def num_vs_num(self,x , y):

        # Calculate covariance and correlation
        covariance = x.cov(y)
        correlation = x.corr(y)

        # Perform linear regression
        slope, intercept, _, _, _ = sc.linregress(x, y)

        # Generate plot 
        fig, ax = plt.subplots(figsize=(8, 6)) #Use ax for plotting
        ax.scatter(x, y, label='Scatter Plot')
        ax.plot(x, slope * x + intercept, color='red', label='Regression Line')
        ax.set_xlabel(x.name) #Use the setter methods of the axes
        ax.set_ylabel(y.name)
        ax.set_title(f'{y.name} vs. {x.name}') #Use the setter methods of the axes
        ax.legend()

        plot = plot_to_base64(fig)
        # Append results to the report
        return [{
            'col1': x.name,
            'col2': y.name,
            'covariance': covariance,                            
            'correlation': correlation,
            'plot': plot,
        }]
    
    def detect_test(self, x, y):
        if np.issubdtype(x.dtype, np.number):  # Check if x is a numeric data type
            x_isnumber = True
        else:
            x_isnumber = False
        if np.issubdtype(y.dtype, np.number):  # Check if x is a numeric data type
            y_isnumber = True
        else:
            y_isnumber = False
            
        if x_isnumber and y_isnumber:
            test_result = self.num_vs_num(x, y)
        elif not(x_isnumber) and not(x_isnumber):
            test_result = self.cat_vs_cat(x, y)
        else:
            test_result = self.num_vs_cat(x, y)
        return test_result
    
    def generate_report(self): # Generate a report
        report_results = []
        df = self.dataframe
        for x in df.columns:
            for y in df.columns:
                if x != y:
                    report_results.extend(self.detect_test(df[x], df[y]))  # Append the *list of dictionaries* here, not the individual dictionaries.
        return report_results

