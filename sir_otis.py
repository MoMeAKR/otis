
import glob
import os
import sys
import json
import re
import momeutils
import subprocess
import mome
import inspect
import shutil 


def extract_subsection_justifications(sample_text = None, sections = None, target_section = None, subsections = None): 
    
    icl_examples = momeutils.load_icl(inspect.currentframe())
    
    
    messages = [
            {"role": "system", "content": """
You are an expert annotator assisting the user in structuring text. You will be provided with a text and a list of sections (for an overview), the target section we want to focus on and its and composing subsections. 
Your task is to identify and extract sentences or text fragments that are relevant to specific subsections within a given target section. 
Answer in a JSON format as follows:
    ```json
    {{
        "extraction_results": [
             {subsections}
        ]
    }} 
    ```
    """.format(subsections = "\n".join(['"{}": ["extracted text fragment that supports the current subsection", ... // add as needed"'.format(subsection.lower().strip().replace(' ', "_")) for subsection in subsections]))}, 
        {"role": "user", "content": " {} For this particular task instance, the following elements are provided:\n Sample Text\n{}\n\n Sections\n{}\n\n Target Section\n{}\n\n Subsections\n{}\n\nGiven a sample text, a list of sections, a target section, and its subsections, extract and return a list of text fragments from the sample text that could serve as justifications or supporting information for each distinct subsection. Try and be accurate and mindful of other sections, that is, not all content must be used and if nothing relates to the current elements, please use null or an empty list.\n\n".format(icl_examples, sample_text, sections, target_section, subsections)}
    ]

    
    results = momeutils.parse_json(momeutils.ask_llm(messages, model = "g4o"))
    momeutils.crprint(json.dumps(results, indent = 4))
    
    return  results["extraction_results"]

def paragraph_writer(paragraph_template = None): 
    
    icl_examples = momeutils.load_icl(inspect.currentframe())
    
    messages = [
            {"role": "system", "content": """
    You are a writing assistant with expertise in producing well-structured and coherent paragraphs. You are expected to generate a paragraph based on a provided template and a set of critical elements. 
    Answer in a JSON format as follows:
    ```json
    {{
    
        "result" : "The generated paragraph based on the provided template and critical elements."
    
    }} 
    ```
    """}, 
        {"role": "user", "content": " {} For this particular task instance, the following elements are provided:\n Paragraph Template\n{}\n\nUse the provided paragraph template to produce a well-structured and coherent paragraph under the key 'result'.\n\n".format(icl_examples, paragraph_template)}
    ]
    
    results = momeutils.parse_json(momeutils.ask_llm(messages, model = "g4o"))
    momeutils.crprint(json.dumps(results, indent = 4))
    
    return results["result"]


def make_theme_template(**kwargs): 
    c = {
        "high_level_context": None, 
        "content": None,
        "things_said_before": None, 
        "where_this_is_going": None,
        "examples": None, 
        "specific_viewpoint": None, 
        "references": None,
        "visuals": None 
    }

    for k, v in kwargs.items():
        if k in c.keys(): 
            c[k] = v
    return c 

def extract_themes_and_illustrations(text_snippet = None): 
    
    icl_examples = momeutils.load_icl(inspect.currentframe())
    
    
    messages = [
            {"role": "system", "content": """
    You are an expert content analyst assisting the user in summarizing textual information. Concretely, you are expected to identify the main themes present in a text snippet.
    Answer in a JSON format as follows:
    ```json
    {{
    
        "themes" : [
        {{
            "main_concept": "a concise description of the main concept 0 in the theme context", 
            "to_insist_and_illustrate": ["critical thing 0 to mention when explaining concept 0", "critical thing 1 to mention when explaining concept 0", ... // add as needed]  
        }},    
    // add more items as needed...
]
    }} 
    ```
    """}, 
        {"role": "user", "content": " {} For this particular task instance, the following elements are provided:\n Text Snippet\n{}\n\nGiven a text snippet, identify the main themes and for each theme, suggest a list of things to illustrate it.\n\n".format(icl_examples, text_snippet)}
    ]
    
    results = momeutils.parse_json(momeutils.ask_llm(messages, model = "g4o"))
    momeutils.crprint(json.dumps(results, indent = 4))
    
    return results["themes"]


def prepare_subsection(config):

    target_text = config['current_contents']
    context = config['higher_level_context']

    out = extract_themes_and_illustrations(target_text)

    subsection = []
    for theme in out: 
        subsection.append([])
        
        if context is None: 
            context = theme['main_concept']
        
        aspects_already_mentionned = []

        for i, current_focus in enumerate(theme['to_insist_and_illustrate']):
            
            next_ = figure_out_next(i, theme, out)
            theme_template = make_theme_template(high_level_context = context, 
                                                content = current_focus, 
                                                things_said_before = list(aspects_already_mentionned) if len(aspects_already_mentionned) > 0 else None,
                                                where_this_is_going = next_)
            aspects_already_mentionned.append(current_focus)
            subsection[-1].append(theme_template)   
    return subsection

def figure_out_next(current_idx, theme, higher_container):
    if current_idx == len(theme['to_insist_and_illustrate']) - 1: 
        if higher_container.index(theme) == len(higher_container) - 1: 
            return "Transition to section conclusion"
        return "Transition to next concepts to illustrate {}".format(higher_container[higher_container.index(theme) + 1]['main_concept'])
    return theme['to_insist_and_illustrate'][current_idx + 1] 

def actually_make_paragraph(structured_contents): 

    paragraphs = []
    for i, paragraph_contents in enumerate(structured_contents): 
        contents = """
Redacting the following subsection: {} 
{}
Specifically, this is paragraph number {} in the subsection. It must revolve around the following content: {}
{}

This paragraph must be constructed in a way that smoothly leads to the following: {}
""".format(structured_contents[0]['high_level_context'], 
          "Previous paragraph contents: {}".format("\n* ".join([""] + paragraph_contents['things_said_before'])) if i > 0 else "",
            i, 
            paragraph_contents['content'], 
            "Desired examples to illustrate the content: {}".format("\n* ".join([""] + paragraph_contents['examples'])) if paragraph_contents['examples'] is not None else "",
            paragraph_contents['where_this_is_going'])
        paragraph = paragraph_writer(contents)
        paragraphs.append(paragraph)
    return "\n\n".join(paragraphs)


def init_config_file(config_path): 
    config = {
        "base_knowledge_path": os.path.join(os.path.dirname(__file__), 'sample_ainimals.txt'),
        "current_contents": None, 
        "higher_level_context": None,
        "current_hash": None,
        "structure_path": os.path.join(os.path.dirname(__file__), 'sir_structure'),
        "interactive_graph_path": os.path.join(os.path.dirname(__file__), 'sir_interactive_graph'),
        "current_base_hash": None, 
        "operating_modules": None, 
        "clipboard_contents": momeutils.get_clipboard(),
        "report_structure": {
            "operation_topic": ["overview", "issues with different methods", "proposed innovation"],
            "technical_justification": ["related works and their limitation", "why we should go in the direction we chose"], 
            "what_we_actually_did": ["overview", "technical details", "results", "discussions"], 
            "conclusion": ["summary", "future work", "concluding remarks"]
        }, 
        "current_report_section_target": None
    }

    with open(config_path, 'w') as f:
        json.dump(config, f, indent = 4)

def load_config(config_path, **kwargs):
    if not os.path.exists(config_path):
        init_config_file(config_path)
    with open(config_path, 'r') as f:
        config = json.load(f)

    nb_updates = 0 
    for k,v in kwargs.items():  
        if k in config.keys():
            nb_updates += 1
            config[k] = v
            if k == "base_contents_path": 
                config['current_base_hash'] = mome.get_short_hash(open(kwargs['base_contents_path']).read(), 15)
                nb_updates += 1 

    if nb_updates > 0:
        momeutils.crline('Updated config file')
    save_config(config, config_path)
    
    return json.load(open(config_path))

def save_config(config, p ): 
    with open(p, 'w') as f:
        json.dump(config, f, indent = 4)

def initiate_graph(graph_path):
    
    mome.init_obsidian_vault(graph_path, exists_ok=True)

def init_sir_otis(config_path = None, **kwargs): 

    config = load_config(config_path, **kwargs)
    initiate_graph(config['interactive_graph_path'])    
    if not os.path.exists(config['structure_path']):
        os.makedirs(config['structure_path'])
    momeutils.crline('Initialized in {}'.format(os.path.dirname(config['interactive_graph_path'])))
    save_config(config, config_path)


def build_sub(config_path = None, **kwargs):
    
    config = load_config(config_path, **kwargs)

    sub_themes = prepare_subsection(config)

    current_hash = mome.get_short_hash(config['current_contents'], 15)
    sub_root = mome.add_node_to_graph(config['interactive_graph_path'],
                                      contents = {"Subsection root": config['current_contents']}, 
                                      tags = ['subsection_root'],  
                                      name_override = current_hash)

    config['current_base_hash'] = current_hash


    for i, sub in enumerate(sub_themes): 


        sub_part_path = mome.add_node_to_graph(config['interactive_graph_path'], 
                                               contents = {"Subsection part {}".format(i): sub[0]['high_level_context']}, tags = ['subsection'], 
                                               parent_path = sub_root, 
                                               node_prefix = "s_{}_{}".format(i, re.sub(r'[^a-zA-Z0-9\s]', '', sub[0]['high_level_context']).strip().lower().replace(' ', '_')),
                                               )

        for j, paragraph in enumerate(sub):
            p = mome.add_node_to_graph(config['interactive_graph_path'], 
                                   contents = {"Structure": "```json\n{}\n```".format(json.dumps(paragraph, indent = 4)),}, 
                                   tags = ['paragraph'], 
                                   parent_path = sub_part_path, 
                                   node_prefix = str(j), 
                                   use_hash = False)

    
    save_config(config, config_path)

def compile(config_path = None, **kwargs): 
    config = load_config(config_path, **kwargs)
    _, paths_to_compile = mome.collect_node_contents(config['interactive_graph_path'], tags = ['subsection'], return_paths = True)

    for p in paths_to_compile:
        links = mome.get_node_links(p)
        contents = [momeutils.parse_json(mome.get_node_section(os.path.join(os.path.dirname(p), l +".md"))) for l in links]
        paragraph = actually_make_paragraph(contents)

        mome.add_section_to_node(p, "Results", paragraph)
   

def high_level_struct(config_path = None, **kwargs): 
    
    config = load_config(config_path, **kwargs)
    base_contents = open(config['base_knowledge_path']).read()
    report_structure = config['report_structure']
    mome.init_obsidian_vault(config['interactive_graph_path'], exists_ok=False)
    base_hash = mome.get_short_hash(base_contents, 15)

    root_node = mome.add_node_to_graph(config['interactive_graph_path'],
                                        contents = {"Base contents": base_contents, 
                                                    "Structure": momeutils.j_deco(report_structure)},
                                        tags = ['root'], 
                                        name_override = base_hash)
    
    config['current_base_hash'] = base_hash 

    for k in report_structure.keys():
        out = extract_subsection_justifications(base_contents, "\n* ".join([""] + list(report_structure.keys())), k, report_structure[k])
        control_params = setup_control_params(out)
        
        section_node = mome.add_node_to_graph(config['interactive_graph_path'],
                                                contents = {"Base contents": momeutils.j_deco({o:"\n* ".join([""] + out[o]) for o in out.keys()}),
                                                            "Control center": momeutils.j_deco(control_params), 
                                                            "Results": ""},
                                                tags = ['section'],
                                                parent_path = root_node, 
                                                node_prefix = re.sub(r'[^a-zA-Z0-9\s]', '', k).strip().lower().replace(' ', '_'), 
                                                use_hash = False)
    
    save_config(config, config_path)

def setup_control_params(suggested_sections): 
    if isinstance(suggested_sections, list): 
        parts = list(suggested_sections)
    elif isinstance(suggested_sections, dict): 
        parts = list(suggested_sections.keys())
    else: 
        raise TypeError('Unrecognized type in setup control params for :{}'.format(type(suggested_sections)))
    
    return {part: {"user_instruction" : None, 
                              "additional_details": None, 
                              "template": "default"} for part in parts}

def get_current_report_config(config):

    root = os.path.join(config['interactive_graph_path'], config['current_base_hash'] + ".md")
    dynasty = mome.collect_dynasty_paths(root, preserve_hierarchy = True)
    dynasty = format_dynasty(dynasty)
    return dynasty

def format_dynasty(dynasty):
    # recursive function that scrolls through the dynasty (path, children) and each path is rewritten as os.path.basename(path)
    # and the children are recursively formatted
    formatted = {"path": os.path.basename(dynasty['path']).split('.')[0], "children": []}
    if len(dynasty['children']) > 0:
        for child in dynasty['children']:
            formatted['children'].append(format_dynasty(child))

    return formatted

def focus_sir(config_path=None, **kwargs):
    config = load_config(config_path, **kwargs)
    if config['current_report_section_target'] == "root":
        config['current_report_section_target'] = config['current_base_hash']
    current_report_structure = get_current_report_config(config)

    done = False
    current_node = current_report_structure
    path = []
    focus_node_name = None

    momeutils.crline('SIR Focus mode: type ".." to move up, a number to move down, or "q" to quit and validate path.\n\n'.upper())

    while not done:
        momeutils.crline("\n\nCurrent location: {}\n".format(current_node['path']))
        if len(current_node['children']) == 0:  
            momeutils.crline("Reached leaf node: {}".format(current_node['path']))
            choice = momeutils.uinput("Select q or ..").strip().lower()
        else: 
            momeutils.crline("Available options:")
            for i, child in enumerate(current_node['children'], 1):
                momeutils.crline(f"  * {i}. {child['path']}")
            

            choice = momeutils.uinput("Selected").strip().lower()

        if choice == 'q':
            done = True
        elif choice == '..':
            if path:
                path.pop()
                current_node = current_report_structure
                for idx in path:
                    current_node = current_node['children'][idx]
                    focus_node_name = current_node['path']
            else:
                momeutils.crline("Already at the root level.")
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(current_node['children']):
                path.append(idx)
                current_node = current_node['children'][idx]
                focus_node_name = current_node['path']
            else:
                momeutils.crline("Invalid option. Please try again.")
        else:
            momeutils.crline("Invalid input. Please enter a number, '..' to move up, or 'q' to quit.")

    config['current_report_section_target'] = focus_node_name
    save_config(config, config_path)
    return path

def node_expansion_colab(config_path = None, **kwargs): 
    config = load_config(config_path, **kwargs)
    focus_node_path = os.path.join(config['interactive_graph_path'], config['current_report_section_target'] + ".md")
    
    parent_hash = mome.get_short_hash(focus_node_path, 15)
    # GETS THE JSON WITH EACH PART (CAN BE SECTION OR SUBSECTION)
    focus_node_contents = momeutils.parse_json(mome.get_node_section(focus_node_path)) # Collects the first section
    focus_node_control = momeutils.parse_json(mome.get_node_section(focus_node_path, "Control center")) 
    
    # check if keys are the same 
    assert list(focus_node_contents.keys()) == list(focus_node_control.keys())

    result_node = mome.add_node_to_graph(config['interactive_graph_path'],
                                        contents = {"Results": ""}, 
                                        tags = ['result_node'],
                                        parent_path = focus_node_path, 
                                        name_override = "results_" + parent_hash,
                                        use_hash = False)
    
    current_tag = mome.get_file_tags(focus_node_path)[0] # CAREFUL FOR THE 0, IN CASE THERE ARE MULTIPLE TAGS AT SOME POINT 
    section_level = len(current_tag.split('_')) + 1
    for i, k in enumerate(focus_node_contents.keys()): 

        if focus_node_control[k]['template'].strip().lower() == "direct": # means that this is going to be directly used to write 
            tag = ['to_compile']
            t = make_theme_template(content = focus_node_contents[k], 
                                    things_said_before = "\n".join([focus_node_contents[kk] for kk in list(focus_node_contents.keys())[:list(focus_node_contents.keys()).index(k)]]),
                                    where_this_is_going = "\n".join([kk for kk in list(focus_node_contents.keys())[list(focus_node_contents.keys()).index(k):]]),
                                    )
            node_contents = {"Structure": momeutils.j_deco(t), "Results" : ""}
        else: 
            section_org = tmp_get_section_org(focus_node_contents[k])
            node_contents = {"Base contents": momeutils.j_deco(section_org), # AI RESULTS 
                             "Control center": momeutils.j_deco(setup_control_params(section_org)), 
                            "Section structure": momeutils.j_deco({"initial_contents": focus_node_contents[k],  # that's the original + some controls (in case we wanna regen)
                                                                   "how_many_subs": 2, 
                                                                    })}
            
            tag = ['sub_' + current_tag]

        new_part = mome.add_node_to_graph(config['interactive_graph_path'],
                                        contents = node_contents,
                                        tags = tag,
                                        parent_path = focus_node_path, 
                                        # node_prefix = k, 
                                        name_override = "sub{}_p{}_{}_{}".format(section_level, i, 
                                                                                 re.sub(r'[^a-zA-Z0-9\s]', '', k).strip().lower().replace(' ', '_'),
                                                                                 parent_hash ),
                                        use_hash = False)

def get_compilable_children(config_path = None, **kwargs):
    config = load_config(config_path, **kwargs)
    focus_node_path = os.path.join(config['interactive_graph_path'], config['current_report_section_target'] + ".md")
    _, paths_to_compile = mome.collect_node_contents(config['interactive_graph_path'], tags = ['to_compile'], return_paths = True)
    dynasty = mome.collect_dynasty_paths(focus_node_path, include_root = False, preserve_hierarchy = True)
    direct_descendants = [p['path'] for p in dynasty["children"]]   
    children_to_compile = [p for p in paths_to_compile if p in direct_descendants]
    
    if "return_dynasty" in kwargs.keys() and kwargs['return_dynasty']:
        return children_to_compile, dynasty
    return children_to_compile

def collect_results_node_in_children(current_node): 
    """
    Collects the results node in the children of the current node
    """
    children = mome.collect_dynasty_paths(current_node, include_root = True, preserve_hierarchy = True)["children"]
    result_nodes_in_children= []
    # momeutils.dj(children)  
    for c in children: 
        if len(c['children']) > 0: 
            for cc in c['children']: 
                if "results" in cc['path']: 
                    result_nodes_in_children.append([c['path'], cc['path']])
    return result_nodes_in_children

def sub_compilation(config_path = None, **kwargs):

    config = load_config(config_path, **kwargs)

    focus_node_path = os.path.join(config['interactive_graph_path'], config['current_report_section_target'] + ".md")
    compilable_children, dynasty = get_compilable_children(config_path = config_path, return_dynasty = True)
    result_in_direct_children = collect_results_node_in_children(focus_node_path)
    momeutils.dj(result_in_direct_children)
    # result_node = [p['path'] for p in dynasty['children'] if "results" in p and mome.get_short_hash(focus_node_path, 15) in p][0] # result node is used to store the results of the compilation
    # direct_children = [p['path'] for p in mome.collect_dynasty_paths(focus_node_path, include_root = True, preserve_hierarchy = True)["children"] if p['path'] != result_node]
    result_node = [p['path'] for p in dynasty['children'] if "results" in p['path'] and mome.get_short_hash(focus_node_path, 15) in p['path']][0]
    direct_children = [p['path'] for p in dynasty['children'] if p['path'] != result_node]
    momeutils.dj({'result': result_node,
        "dc": direct_children})
    results = []
    for i, c in enumerate(direct_children):
        if c in compilable_children: # direct nodes to compile 
            results.append(tmp_compilation("hello --> needs compilation from {}".format(c)))
        elif c in [r[0] for r in result_in_direct_children]: # children nodes that have a result node 
            results.append("Node {}: Already compiled --> Contents: {}".format(c, mome.get_node_section([r[1] for r in result_in_direct_children if r[0] == c][0], "Results")))
        else: # other node missing compilation
            results.append("Node {}: TODO".format(i))
    input("\n".join(results))
    mome.update_section(result_node, "Results", "\n\n".join(results))


def get_compilable_nodes(config_path = None, **kwargs):
    config = load_config(config_path, **kwargs)
    _, paths_to_compile = mome.collect_node_contents(config['interactive_graph_path'], tags = ['to_compile'], return_paths = True)
    momeutils.dj(paths_to_compile)
    return paths_to_compile

def tmp_compilation(node_contents): 
    return "My man! "

def tmp_get_section_org(section_content):   
    sentences = section_content.split('.')

    ks = {" ".join(s.split()[-2:]).strip().replace(' ', '_'): s for s in sentences if len(s) > 0}
    return ks 

def tmp_save(config_path= None, **kwargs): 
    config = load_config(config_path, **kwargs)
    graph_path = config['interactive_graph_path']
    save_path= graph_path + "_safe"
    if os.path.exists(save_path): 
        shutil.rmtree(save_path)
    shutil.copytree(graph_path, save_path)
    
def tmp_load(config_path = None, **kwargs): 
    config = load_config(config_path, **kwargs)
    graph_path = config['interactive_graph_path']
    save_path= graph_path + "_safe"
    if os.path.exists(graph_path): 
        shutil.rmtree(graph_path)
    shutil.copytree(save_path, graph_path)


# def node_colab(config_path = None, **kwargs): 
    
#     config = load_config(config_path, **kwargs)

#     focus_node_path = os.path.join(config['interactive_graph_path'], config['current_report_section_target'] + ".md")
#     focus_node_contents = momeutils.parse_json(mome.get_node_section(focus_node_path)) # Collects the first section 




    
if __name__ == "__main__": 

    # focus_sir(config_path = os.path.join(os.path.dirname(__file__), 'sir_otis_config.json'), current_report_section_target = "root")

    # node_expansion_colab(config_path = os.path.join(os.path.dirname(__file__), 'sir_otis_config.json'), current_report_section_target = "operationtopic_b68ab377e8ecfc0")
    # momeutils.uinput('Change one element in the control center to "direct" and run the node_expansion_colab function again | this should be a function')
    # node_expansion_colab(config_path = os.path.join(os.path.dirname(__file__), 'sir_otis_config.json'), current_report_section_target = "sub2_p2_proposedinnovation_7462b936de74962")

    # ================== Let's try to build a subsection
    # get_compilable_children(config_path = os.path.join(os.path.dirname(__file__), 'sir_otis_config.json'))
    # sub_compilation(config_path = os.path.join(os.path.dirname(__file__), 'sir_otis_config.json'), current_report_section_target = "sub2_p2_proposedinnovation_7462b936de74962")
    sub_compilation(config_path = os.path.join(os.path.dirname(__file__), 'sir_otis_config.json'), current_report_section_target = "operationtopic_b68ab377e8ecfc0")


    # text = "Neural networks limitations relative to OOD samples and spurrious correlations"
    # text= "Collecting labels for supervised learning methods is dauting and expensive and may not capture real world dynamics. What if we were able to produce synthetic data in which the true signal is known ?"

    # r = prepare_subsection(text, "Illustrating known limitation of neural nets to introduce our method on synthetic training ")
    # # # # tmp_save 
    # path= os.path.join(os.path.dirname(__file__), "tmp_sir", "tmp_save.json")
    # if not os.path.exists(os.path.dirname(path)):
    #     os.makedirs(os.path.dirname(path))
    # with open(path, 'w') as f:
    #     json.dump(r, f, indent = 4)

    # # # tmp_load
    # r = json.load(open(path))
    
    # result = []
    # for ii in r: 
    #     result.append(actually_make_paragraph(ii))
    #     input("\n".join(result))
