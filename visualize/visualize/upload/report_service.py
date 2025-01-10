from flask import Flask, jsonify, request
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as sc
import base64, io
import scipy as sc
app = Flask(__name__)

@app.route('/report', methods=['POST'])
def generate_report():
    try:
        file_content = request.files['file'].read()  # Get file from request
        df = pd.read_csv(io.StringIO(file_content.decode('utf-8'))) # Decode and read CSV

        num_cols = df.select_dtypes(include=['number']).columns

        results = []  # Store results for each pair of columns

        num_cols = list(num_cols)
        for i in range(len(num_cols)):
            for j in range(i + 1, len(num_cols)):
                col1 = num_cols[i]
                col2 = num_cols[j]

                covariance = np.cov(df[col1], df[col2])[0, 1]
                correlation = np.corrcoef(df[col1], df[col2])[0, 1]

                # Linear Regression
                slope, intercept, _, _, _ = sc.linregress(df[col1], df[col2])

                
                # Generate plot and encode to base64
                plt.figure(figsize=(8, 6))
                plt.plot(df[col1], slope * df[col1] + intercept, c='red')
                plt.scatter(df[col1], df[col2])
                plt.title(f'{col2} vs. {col1}')
                plt.xlabel(col1)
                plt.ylabel(col2)

                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                plot_data = base64.b64encode(buf.read()).decode('utf-8')
                buf.close()
                plt.clf()  # Clear the plot


                results.append({
                    "col1": col1,
                    "col2": col2,
                    "covariance": covariance,
                    "correlation": correlation,
                    "plot": plot_data
                })



        return jsonify(results)



    except Exception as e:
        print(f"Error generating report: {e}")
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True, port=5001)

