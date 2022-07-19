from django.shortcuts import render
from django.http import HttpResponse
import pandas as pd
from connector.cnxn import server_access
from math import ceil


# Create your views here.
def index(request):
    return render(request, 'form.html')

def calculate_tariff(request):

    AWB = request.POST["AWB"]
    HAWB = request.POST["HAWB"]
    arrival_date = request.POST["arrival_date"]
    payment_date = request.POST["payment_date"]
    category = request.POST["category"]
    cargo_class = request.POST["cargo_class"]
    weight = request.POST["weight"]

    calculations_sql = '''
     DECLARE @AWB nvarchar(255) 
    DECLARE @HAWB nvarchar(255) 
    DECLARE @Arrival_Date date 
    DECLARE @Payment_Date date 
    DECLARE @Category nvarchar(50) 
    DECLARE @Cargo_Class nvarchar(50) 
    DECLARE @Weight float 

    SET @AWB = '{}'
    SET @HAWB = '{}'
    SET @Arrival_Date = '{}';
    SET @Payment_Date = '{}';
    SET @Category = '{}';
    SET @Cargo_Class = '{}';
    SET @Weight = {};

    SELECT t.*
    ,CASE WHEN HAWB IS NOT NULL THEN doc.Charges_D_Console ELSE 0 END AS [Deconsole Charges]
    ,CASE WHEN HAWB IS NOT NULL THEN 0 ELSE doc.Charges_DO_Fee END AS [DO Fee]
    ,doc.Charges_Doc [Documentation Charges]
    ,CASE WHEN hd.Charges_Per = 'Per KG' THEN hd.Charges_PKR * Weight ELSE hd.Charges_PKR END AS [Handling]
    ,CASE WHEN gd.Charges_Per = 'Per Day' THEN (Dwell_Time - gd.Free_Days) * gd.Charges_PKR ELSE 
    (Dwell_Time - gd.Free_Days) * gd.Charges_PKR * Weight END as [Storage]
    ,CEILING((CASE WHEN HAWB IS NOT NULL THEN doc.Charges_D_Console ELSE 0 END) + 
     (CASE WHEN HAWB IS NOT NULL THEN 0 ELSE doc.Charges_DO_Fee END) + 
     (doc.Charges_Doc) +
     (CASE WHEN hd.Charges_Per = 'Per KG' THEN hd.Charges_PKR * Weight ELSE hd.Charges_PKR END) +
     (CASE WHEN gd.Charges_Per = 'Per Day' THEN (Dwell_Time - gd.Free_Days) * gd.Charges_PKR ELSE 
    (Dwell_Time - gd.Free_Days) * gd.Charges_PKR * Weight END)) Total

    FROM (
    SELECT @AWB [AWB]
    		,@HAWB [HAWB]
    		,@Arrival_Date Arrival_Date
    		,@Payment_Date Payment_Date
    		,@Category Category
    		,@Cargo_Class Cargo_Class
    		,@Weight [Weight]
    		,DATEDIFF(day, @Arrival_Date, @Payment_Date) + 1 [Dwell_Time]
    		) t
    		LEFT JOIN [dbo].[Tariff_Handling] hd
    		ON  hd.Cargo_Class = t.Cargo_Class
    		AND hd.Category = t.Category 
    		AND ROUND(t.Weight,2) >= hd.Wt_Min
    		AND ROUND(t.Weight,2) <= hd.Wt_Max
    		AND CONVERT(DATE, Payment_Date) >= hd.Effective_Date
    		AND CONVERT(DATE, Payment_Date) <= hd.[Expiry_Date]


    		LEFT JOIN [dbo].[Tariff_Godown] gd ON
    		gd.Cargo_Class = t.Cargo_Class
    		AND gd.Category = t.Category
    		AND ROUND(t.Weight ,2) >= gd.Wt_Min
    		AND ROUND(t.Weight ,2) <= gd.Wt_Max
    		AND ROUND(t.Dwell_Time,2) >= gd.Dwell_Min
    		AND ROUND(t.Dwell_Time,2) <= gd.Dwell_Max
    		AND CONVERT(DATE, Payment_Date) >= gd.Effective_Date
    		AND CONVERT(DATE, Payment_Date) <= gd.[Expiry_Date]
    

    		LEFT JOIN [dbo].[Tariff_Doc] doc ON
    		doc.Category = t.Category
    		AND CONVERT(DATE, Payment_Date) >= doc.Effective_Date
    		AND CONVERT(DATE, Payment_Date) <= doc.[Expiry_Date]

    
    
    '''.format(AWB, HAWB, arrival_date, payment_date, category, cargo_class, weight)

    cnxn = server_access('CARGO')
    df = pd.read_sql(calculations_sql, cnxn)
    # dwell_time = round(df['Dwell_Time'].values[0],2)
    # deconsole = round(df['Deconsole Charges'].values[0],2)
    # do = round(df['DO Fee'].values[0],2)
    # handling = round(df['Handling'].values[0],2)
    # storage = round(df['Storage'].values[0],2)
    # total = round(df['Total'].values[0],0)
    dwell_time = ceil(df['Dwell_Time'].values[0])
    deconsole = ceil(df['Deconsole Charges'].values[0])
    do = ceil(df['DO Fee'].values[0])
    handling = ceil(df['Handling'].values[0])
    storage = ceil(df['Storage'].values[0])
    total = ceil(df['Total'].values[0])
    dwell_time = f"{dwell_time:,}"
    deconsole = f"{deconsole:,}"
    do = f"{do:,}"
    handling = f"{handling:,}"
    storage = f"{storage:,}"
    total = f"{total:,}"
    return render(request, 'calculations.html', {'AWB':AWB, 'HAWB':HAWB, 'arrival_date':arrival_date, 
    'payment_date':payment_date, 'category':category, 'cargo_class':cargo_class, 'weight':weight,
    'dwell_time':dwell_time, 'deconsole':deconsole, 'do':do, 'handling':handling, 'storage':storage, 'total':total})