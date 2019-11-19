# Import libraries
import datetime
import glob
import numpy as np
import os
import sys

# Import scripts
from json2status import json2status
from json2timeline import json2timeline
from html2email import html2email

###################################################################################################
def simple_perf_test(wtimes, stdCoeff = 2.0):
    '''
    Simple performance test
    Returns:
        status, measured, mean, std
    Status:
        'pass' if test is within 2 standard deviations of the mean
        'warn' if the above is false but the previous test passes  (This is done to avoid spikes)
        'fail' otherwise
    '''
    # Compute mean and std
    wt = np.asarray(wtimes, dtype=np.float64)
    mu = np.mean(wt)
    sig = np.std(wt)

    # Performance test
    if abs(wt[-1] - mu) < stdCoeff*sig:
        status = 'pass'
    elif abs(wt[-2] - mu) < stdCoeff*sig:
        status = 'warn'
    else:
        status = 'fail'
    return status, wt[-1], mu, sig

###################################################################################################
def build_perf_tests(files, cases, nps, timers):
    '''
    Returns dictionary with performance tests
    '''
    # Loop over cases
    perfTests = {}
    colorMap = {'pass':'green','warn':'yellow','fail':'red'}
    for case in cases:
        name = case + '_np' + str(nps)
        perfTests[name] = {}
        testDict = perfTests[name]

        # Extract test status
        dates, status = json2status(files, case, nps)
        if status[-1]:
            testDict['runTest'] = 'Passed'
            testDict['runTestColor'] = 'green'

            # Loop over timers
            testDict['timers'] = {}
            colorCounter = {'green':0,'yellow':0,'red':0}
            for timer in timers:
                testDict['timers'][timer] = {}
                timerDict = testDict['timers'][timer]

                # Extract timer data and run performance test
                dates, wtimes = json2timeline(files, case, nps, timer, False)
                perfStatus, timerDict['measured'], timerDict['mean'], timerDict['std'] = simple_perf_test(wtimes, 2.0)

                # Extract performance test status
                color = colorMap[perfStatus]
                timerDict['perfTestColor'] = color
                colorCounter[color] = colorCounter[color] + 1

            # Extract overall performance tests status
            testDict['perfTests'] = '{}/{}/{}'.format(colorCounter['green'],colorCounter['yellow'],colorCounter['red'])
            if colorCounter['red']:
                testDict['perfTestsColor'] = 'red'
            elif colorCounter['yellow']:
                testDict['perfTestsColor'] = 'yellow'
            else:
                testDict['perfTestsColor'] = 'green'

        # Failed test
        else:
            testDict['runTest'] = 'Failed'
            testDict['runTestColor'] = 'red'
            testDict['perfTests'] = 'Failed'
            testDict['perfTestsColor'] = 'red'

    return perfTests

###################################################################################################
def build_perf_tests_html(perfTests):
    '''
    Returns html string with performance status report
    '''
    # Styles
    style = '''
    <style>
        table,th,td
        {
            border: 2px solid black;
            text-align: center;
        }
        table
        {
            border-collapse: collapse;
            width: 90%;
        }
        th
        {
            color: white;
            background-color: gray;
        }
        td
        {
            height: 40px;
        }
        tr:nth-child(even)
        {
            background-color: #D0D0D0;
        }
        tr:nth-child(odd)
        {
            background-color: #F0F0F0;
        }
        #green
        {
            background-color: green;
            color: white;
        }
        #yellow
        {
            background-color: yellow;
        }
        #red
        {
            background-color: red;
            color: white;
        }
    </style>
    '''

    # Title
    title = '''
    <font size="+2"><b>Albany Land Ice Performance Status Report on Blake</b></font>
    <br><br>
    '''

    # Status Table
    statusTab = '''
    <table>
        <caption><font size="+2"><b>Status</b></font></caption>
        <tr>
            <th>Name</th>
            <th>Run Test</th>
            <th>Performance Tests (Passes/Warnings/Fails)</th>
        </tr>
    '''
    for name, info in perfTests.items():
        row = '''
        <tr>
            <td>{}</td>
            <td id="{}">{}</td>
            <td id="{}">{}</td>
        </tr>
        '''.format(name,info['runTestColor'],info['runTest'],info['perfTestsColor'],info['perfTests'])
        statusTab = statusTab + row
    statusTab = statusTab + '''
    </table>
    '''

    # Subject and Timer Tables
    subjectTestsFailed = False
    timerTabs = ''
    for name, info in perfTests.items():
        if info['runTest'] == 'Failed':
            subjectTestsFailed = True
            timerTabs = timerTabs + '''
            <br><br>
            <font size="+1">{} test failed...</font>
            '''.format(name)
            continue
        else:
            timerTab = '''
            <br><br>
            <table>
                <caption><font size="+2"><b>{} Timers (s)</b></font></caption>
                <tr>
                    <th>Timer</th>
                    <th>Measured</th>
                    <th>Mean</th>
                    <th>Std</th>
                </tr>
            '''.format(name)
            for timer, timerInfo in info['timers'].items():
                row = '''
                <tr>
                    <td>{}</td>
                    <td id="{}">{:g}</td>
                    <td>{:g}</td>
                    <td>{:g}</td>
                </tr>
                '''.format(timer,timerInfo['perfTestColor'],timerInfo['measured'],timerInfo['mean'],timerInfo['std'])
                timerTab = timerTab + row

                if timerInfo['perfTestColor'] == 'red':
                    subjectTestsFailed = True
            timerTab = timerTab + '''
            </table>
            '''
            timerTabs = timerTabs + timerTab
    subject = 'Albany Land Ice Performance Tests'
    if subjectTestsFailed:
        subject = '[ALIPerfTestsFailed] ' + subject
    else:
        subject = '[ALIPerfTestsPassed] ' + subject

    # Links
    date = datetime.datetime.today().strftime('%m_%d_%Y')
    testLogsLink = 'https://my.cdash.org/index.php?subproject=IKTBlakeALIPerformTests&project=Albany'
    notebookHtmlLink = 'https://ikalash.github.io/ali/blake_nightly_data/Ali_PerfTestsBlake_' + date + '.html'
    notebookLink = 'https://mybinder.org/v2/gh/ikalash/ikalash.github.io/master?filepath=ali/blake_nightly_data%2FAli_PerfTestsBlake.ipynb'
    links = '''
    <br>
    Click <a href="{}">here</a> for test logs, <a href="{}">here</a> for more details on performance or <a href="{}">here</a> for an interactive notebook of the data.
    '''.format(testLogsLink, notebookHtmlLink, notebookLink)

    return subject, style + title + statusTab + timerTabs + links

###################################################################################################
if __name__ == "__main__":
    '''
    Send email showing status report of performance tests
    '''
    # Email inputs
    sender = 'jwatkin@sandia.gov'
    #recipients = ['jwatkin@sandia.gov']
    #recipients = ['jwatkin@sandia.gov','ikalash@sandia.gov']
    recipients = ['jwatkin@sandia.gov','ikalash@sandia.gov','mperego@sandia.gov','lbertag@sandia.gov']

    # Pass directory name
    if len(sys.argv) < 2:
        dir = ''
    else:
        dir = sys.argv[1]

    # Extract file names
    files = glob.glob(os.path.join(dir,'ctest-*'))

    # If today's json file doesn't exist, send error message
    date = datetime.datetime.today().strftime('%Y%m%d')
    files_with_date = [filename for filename in files if date in filename]
    if not files_with_date:
        print("Today's json doesn't exist, sending error email...")
        html2email('[ALIPerfTestsFailed] Albany Land Ice Performance Tests',
                '''
                <b>Error: Today's json file doesn't exist!</b>
                <br><br>
                Click <a href="https://my.cdash.org/index.php?subproject=IKTBlakeALIPerformTests&project=Albany">here</a> for test logs and
                <a href="https://github.com/ikalash/ikalash.github.io/tree/master/ali/blake_nightly_data">here</a> for the repo.
                ''',
                sender, ['jwatkin@sandia.gov','ikalash@sandia.gov'])
                #sender, ['jwatkin@sandia.gov'])
        sys.exit()

    # Specify case to extract from ctest.json file
    cases = ('ant-2-20km_ml_line','ant-2-20km_muelu_line','ant-2-20km_muelu_decoupled_line')

    # Specify number of processes to extract from ctest.json file
    nps = 384

    # Specify timers to extract from ctest.json file (note: must be unique names per test in file)
    timers = ('Albany: Total Time:',
              'Albany: **Total Fill Time**:',
              'NOX Total Preconditioner Construction:',
              'NOX Total Linear Solve:')

    # Run performance tests and build dictionary
    print("Running performance analysis...")
    perfTests = build_perf_tests(files, cases, nps, timers)
    #print(perfTests)

    # Build html string
    print("Building HTML...")
    subject, perfTestsHTML = build_perf_tests_html(perfTests)
    #print(perfTestsHTML)

    # Email status report
    print("Sending email...")
    html2email(subject, perfTestsHTML, sender, recipients)

