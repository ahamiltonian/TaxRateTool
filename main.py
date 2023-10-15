# This is a Tax Rate Analysis Tool

# imports
from pandas import __version__ as pandas_version
from bokeh import __version__ as bokeh_version
from numpy import __version__ as numpy_version

import pandas as pd
import numpy as np
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, CustomJS, Slider, Span
from bokeh.palettes import Spectral9
from bokeh.plotting import figure, show, save, output_file
from bokeh.transform import factor_cmap
from bokeh.models.widgets import Div


# import sandbox

# check imports and print versions
def check_imports() -> None:
    print("Pandas - %s" % pandas_version)
    print("Bokeh - %s" % bokeh_version)
    print("Numpy - %s" % numpy_version)


# plot the tax burden for each sector
def plot_burden() -> None:
    # list of sectors
    sectors = ['Residential',
               'Business',
               'Utilities',
               'Light_Industry',
               'Port_Property',
               'Port_Improvement',
               'Recreation',
               'Forests',
               'Farm']

    # dictionary of property values (in millions of dollars) with sector name as key
    prop_value_current = dict(zip(sectors, np.array([11044.472335,  # 'Residential'
                                                  1840.787650,      # 'Business'
                                                  56.503260,        # 'Utilities'
                                                  118.545800,       # 'Light_Industry'
                                                  21.001570,        # 'Port_Property'
                                                  4.476430,         # 'Port_Improvement'
                                                  32.735500,        # 'Recreation'
                                                  1.897900,         # 'Forests'
                                                  0.052110])))      # 'Farm'

    prop_value_previous = dict(zip(sectors, np.array([11044.472335, # 'Residential'
                                                  1840.787650,      # 'Business'
                                                  56.503260,        # 'Utilities'
                                                  118.545800,       # 'Light_Industry'
                                                  21.001570,        # 'Port_Property'
                                                  4.476430,         # 'Port_Improvement'
                                                  32.735500,        # 'Recreation'
                                                  1.897900,         # 'Forests'
                                                  0.052110])))      # 'Farm'

    # dictionary of mil rate with sector name as key
    rate_current = dict(zip(sectors, np.array([2.1246,  # 'Residential'
                                            5.3115,     # 'Business'
                                            40.0000,    # 'Utilities'
                                            8.1160,     # 'Light_Industry'
                                            27.5000,    # 'Port_Property'
                                            22.5000,    # 'Port_Improvement'
                                            2.1246,     # 'Recreation'
                                            5.3115,     # 'Forests'
                                            2.1246])))  # 'Farm'
    rate_previous = dict(zip(sectors, np.array([2.1246,  # 'Residential'
                                            5.3115,     # 'Business'
                                            40.0000,    # 'Utilities'
                                            8.1160,     # 'Light_Industry'
                                            27.5000,    # 'Port_Property'
                                            22.5000,    # 'Port_Improvement'
                                            2.1246,     # 'Recreation'
                                            5.3115,     # 'Forests'
                                            2.1246])))

    # default (ie. current year) burden per sector is the rate * property value per sector
    burden_current = dict(
        zip(sectors, np.array(list(rate_current.values())) * np.array(list(prop_value_current.values())) / 1000))
    burden_previous = dict(
        zip(sectors, np.array(list(rate_previous.values())) * np.array(list(prop_value_previous.values())) / 1000))

    # tax burden data
    burden_df = pd.DataFrame({'Residential': [burden_current['Residential'], burden_previous['Residential']],
                              'Business': [burden_current['Business'], burden_previous['Business']],
                              'Utilities': [burden_current['Utilities'], burden_previous['Utilities']],
                              'Light_Industry': [burden_current['Light_Industry'], burden_previous['Light_Industry']],
                              'Port_Property': [burden_current['Port_Property'], burden_previous['Port_Property']],
                              'Port_Improvement': [burden_current['Port_Improvement'], burden_previous['Port_Improvement']],
                              'Recreation': [burden_current['Recreation'], burden_previous['Recreation']],
                              'Forests': [burden_current['Forests'], burden_previous['Forests']],
                              'Farm': [burden_current['Farm'], burden_previous['Farm']],
                              'year': ['2024', '2023']})
    # print(burden_df)
    burden_cds = ColumnDataSource(data=burden_df)

    # create horizontal stack plot of tax revenue by sector and year
    p = figure(y_range=['2024', '2023'], x_range=(0, 55),
               width=700, height=350,
               title='Tax Revenue (in Millions) by Sector and Year (vertical line is revenue required)',
               x_axis_label='Tax Revenue (Millions of $)',
               tooltips="$name Revenue: $@$name{0.00}M")
    p.hbar_stack(stackers=sectors, y='year', height=0.7, color=Spectral9, muted_alpha=0.5, legend_label=sectors,
                 source=burden_cds)
    p.legend.location = "top_right"
    p.legend.click_policy = "mute"

    # add the line the total revenue required
    revenue_required_previous = 37.220
    revenue_required_current = 41.070
    revenue_required_line_previous = Span(location=revenue_required_previous, dimension='height',
                                      line_color='grey', line_width=1, line_alpha=0.5)
    revenue_required_line_current = Span(location=revenue_required_current, dimension='height',
                                      line_color='black', line_width=3, line_alpha=0.5)
    p.add_layout(revenue_required_line_previous)
    p.add_layout(revenue_required_line_current)

    # get the burden difference from previous year
    # there must be a cleaner way to do this
    diff_dict = {}
    for sector in sectors:
        diff = 100 * (burden_df[sector][0] - burden_df[sector][1]) / burden_df[sector][1]
        diff_dict[sector] = diff
    diff_cds = ColumnDataSource(data=dict(sector=list(diff_dict.keys()), diff=list(diff_dict.values())))

    # plot for the tax rate change from previous year
    q = figure(x_range=sectors, y_range=(-25, 25), height=250, width=700, toolbar_location='right',
               title="% Change per Sector", tooltips="@diff{0.0}%")

    q.vbar(x='sector', top='diff', width=0.9, source=diff_cds,
           line_color='white', fill_color=factor_cmap('sector', palette=Spectral9, factors=sectors))

    # text box to tell user if they have met revenue requirements
    #box_color = ['forestgreen']
    #box_text = ['just right']
    box_color = ['white']
    box_text = ['try a slider']

    # create a data source to enable refreshing of fill & text color
    box_cds = ColumnDataSource(data=dict(color=box_color, text=box_text))
    r = figure(x_range=(-8, 8), y_range=(-4, 4),
               width=300, height=100,
               title='Are revenue requirements met? (within $10k)', tools='')
    r.rect(0, 0, width=18, height=10, fill_color='color',
           line_color='black', source=box_cds)
    r.text(0, 0, text='text', text_color='white',
           alpha=1.0, text_font_size='18px', text_baseline='middle',
           text_align='center', source=box_cds)
    r.xaxis.visible = False
    r.yaxis.visible = False

    # make the sliders
    res_rate_slider = Slider(start=rate_current['Residential'] - 0.5, end=rate_current['Residential'] + 0.5,
                             value=rate_current['Residential'], step=0.001, format='0.000',
                             title='Residential Tax Rate')
    utl_rate_slider = Slider(start=rate_current['Utilities'] - 0.0001, end=rate_current['Utilities'],
                             value=rate_current['Utilities'], step=0.1, format='0.000',
                             title='Utilities Tax Rate (fixed at 40.000)')
    ptp_rate_slider = Slider(start=rate_current['Port_Property'] - 0.0001, end=rate_current['Port_Property'],
                             value=rate_current['Port_Property'], step=0.1, format='0.000',
                             title='Port Property Tax Rate (fixed at 27.500)')
    pti_rate_slider = Slider(start=rate_current['Port_Improvement'] - 0.0001, end=rate_current['Port_Improvement'],
                             value=rate_current['Port_Improvement'], step=0.1, format='0.000',
                             title='Port Improvement Tax Rate (fixed at 22.500)')
    ind_rate_slider = Slider(start=rate_current['Light_Industry'] - 2, end=rate_current['Light_Industry'] + 2,
                             value=rate_current['Light_Industry'], step=0.005, format='0.000',
                             title='Light Industry Tax Rate')
    bus_rate_slider = Slider(start=rate_current['Business'] - 2, end=rate_current['Business'] + 2,
                             value=rate_current['Business'], step=0.005, format='0.000',
                             title='Business Tax Rate')
    fst_rate_slider = Slider(start=rate_current['Forests'] - 2, end=rate_current['Forests'] + 2,
                             value=rate_current['Forests'], step=0.005, format='0.000',
                             title='Forests Tax Rate')
    rec_rate_slider = Slider(start=rate_current['Recreation'] - 2, end=rate_current['Recreation'] + 2,
                             value=rate_current['Recreation'], step=0.001, format='0.000',
                             title='Recreation Tax Rate')
    frm_rate_slider = Slider(start=rate_current['Farm'] - 2, end=rate_current['Farm'] + 2,
                             value=rate_current['Farm'], step=0.001, format='0.000',
                             title='Farm Tax Rate')

    slider_callback = CustomJS(
        args=dict(sedit=burden_cds, prop_value=prop_value_current, sdiff=diff_cds,
                  revenue_required=revenue_required_current, sbox=box_cds,
                  res_rate_slider=res_rate_slider,
                  utl_rate_slider=utl_rate_slider,
                  ptp_rate_slider=ptp_rate_slider,
                  pti_rate_slider=pti_rate_slider,
                  ind_rate_slider=ind_rate_slider,
                  bus_rate_slider=bus_rate_slider,
                  fst_rate_slider=fst_rate_slider,
                  rec_rate_slider=rec_rate_slider,
                  frm_rate_slider=frm_rate_slider),
        code="""
        const bs = sedit.data;
        const res_burden = res_rate_slider.value*prop_value['Residential']/1000;
        const utl_burden = utl_rate_slider.value*prop_value['Utilities']/1000;
        const ptp_burden = ptp_rate_slider.value*prop_value['Port_Property']/1000;
        const pti_burden = pti_rate_slider.value*prop_value['Port_Improvement']/1000;
        const ind_burden = ind_rate_slider.value*prop_value['Light_Industry']/1000;
        const bus_burden = bus_rate_slider.value*prop_value['Business']/1000;
        const fst_burden = fst_rate_slider.value*prop_value['Forests']/1000;
        const rec_burden = rec_rate_slider.value*prop_value['Recreation']/1000;
        const frm_burden = frm_rate_slider.value*prop_value['Farm']/1000;

        // modify the burden data
        sedit.data = {
            Residential: [res_burden, bs['Residential'][1]],
            Utilities: [utl_burden, bs['Utilities'][1]],
            Port_Property: [ptp_burden, bs['Port_Property'][1]],
            Port_Improvement: [pti_burden, bs['Port_Improvement'][1]],
            Light_Industry: [ind_burden, bs['Light_Industry'][1]],
            Business: [bus_burden, bs['Business'][1]],
            Forests: [fst_burden, bs['Forests'][1]],
            Recreation: [rec_burden, bs['Recreation'][1]],
            Farm: [frm_burden, bs['Farm'][1]],
            year: bs.year
            }

        // make the change in tax rate per sector plot
        const ds = sdiff.data;
        const res_diff = 100 * (res_burden - bs['Residential'][1]) / bs['Residential'][1]
        const utl_diff = 100 * (utl_burden - bs['Utilities'][1]) / bs['Utilities'][1]
        const ptp_diff = 100 * (ptp_burden - bs['Port_Property'][1]) / bs['Port_Property'][1]
        const pti_diff = 100 * (pti_burden - bs['Port_Improvement'][1]) / bs['Port_Improvement'][1]
        const ind_diff = 100 * (ind_burden - bs['Light_Industry'][1]) / bs['Light_Industry'][1]
        const bus_diff = 100 * (bus_burden - bs['Business'][1]) / bs['Business'][1]
        const fst_diff = 100 * (fst_burden - bs['Forests'][1]) / bs['Forests'][1]
        const rec_diff = 100 * (rec_burden - bs['Recreation'][1]) / bs['Recreation'][1]
        const frm_diff = 100 * (frm_burden - bs['Farm'][1]) / bs['Farm'][1]
        sdiff.data = {
            sector: ['Residential', 'Utilities', 'Port_Property', 'Port_Improvement', 'Light_Industry', 'Business', 'Forests', 'Recreation', 'Farm'],
            diff: [res_diff, utl_diff, ptp_diff, pti_diff, ind_diff, bus_diff, fst_diff, rec_diff, frm_diff],
        }

        // check if the total revenue target is met
        const revenue = res_burden + utl_burden + ptp_burden + pti_burden + ind_burden + bus_burden + fst_burden + rec_burden + frm_burden;
        const balance = revenue_required - revenue;
        const epsilon = 0.01;  // this is in Millions, so 0.01 = $10k
        if ( balance < -1*epsilon ){
            sbox.data = { color: ['black'], text: ['$'+-1*balance.toFixed(2)+'M too much'] };
        }
        else if ( balance > epsilon ){
            sbox.data = { color: ['darkred'], text: ['$'+balance.toFixed(2)+'M too little'] };
        }
        else{
            sbox.data = { color: ['forestgreen'], text: ['just right'] };
        }

    """)

    res_rate_slider.js_on_change('value', slider_callback)
    bus_rate_slider.js_on_change('value', slider_callback)
    utl_rate_slider.js_on_change('value', slider_callback)
    ind_rate_slider.js_on_change('value', slider_callback)
    ptp_rate_slider.js_on_change('value', slider_callback)
    pti_rate_slider.js_on_change('value', slider_callback)
    rec_rate_slider.js_on_change('value', slider_callback)
    fst_rate_slider.js_on_change('value', slider_callback)
    frm_rate_slider.js_on_change('value', slider_callback)

    # show(row(column(p, Div(text='', height=20), q), Div(text='', width=50),
    #          column(Div(text='', height=50),
    #                 res_rate_slider,
    #                 bus_rate_slider,
    #                 utl_rate_slider,
    #                 ind_rate_slider,
    #                 ptp_rate_slider,
    #                 pti_rate_slider,
    #                 rec_rate_slider,
    #                 fst_rate_slider,
    #                 frm_rate_slider,
    #                 r)))

    output_file("tax_rate_tool.html")
    save(row(column(p, Div(text='', height=20), q), Div(text='', width=50),
             column(Div(text='', height=50),
                    res_rate_slider,
                    bus_rate_slider,
                    utl_rate_slider,
                    ind_rate_slider,
                    ptp_rate_slider,
                    pti_rate_slider,
                    rec_rate_slider,
                    fst_rate_slider,
                    frm_rate_slider,
                    r)))

# run main
if __name__ == '__main__':
    check_imports()
    plot_burden()
    # sandbox.test_dataframe()
