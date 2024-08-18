import momeutils 
import json 
import os 



def synthesize(node_contents):
    print(node_contents)
    out=momeutils.basic_task('Initial transcription: {}\n\n\n As an astute pitcher, make a more condensed and efficient version of the above, use the transcription language'.format(node_contents), model = 'flash')
    print(out)
    # input('synthsize above')
    return out 

def bullets_from_synthesis(node_contents):
    print('='*10)
    print(node_contents)
    out = momeutils.basic_task('Target text: {}\n\n\n As an astute and efficient presenter, suggest between three and five bullet points that would support the presentation of the above, use the transcription language'.format(node_contents), model = 'flash')
    print(out)
    # input('bullets from synthesis')
    return out 

def suggest_diagram(node_contents):
    print('*'*10)
    print(node_contents)
    out  = momeutils.basic_task('Target text: {}\n\n\n As a skilled diagrammer, suggest a diagram that would support the presentation of the above, use the transcription language'.format(node_contents), model = 'flash')
    print(out)
    # input('suggest diagram')
    return out


def my_test(node_contents): 
    return len(node_contents)