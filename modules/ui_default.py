import gradio as gr

from modules import shared, ui, utils
from modules.prompts import count_tokens, load_prompt
from modules.text_generation import (
    generate_reply_wrapper,
    stop_everything_event
)
from modules.utils import gradio


def create_ui():
    default_text = load_prompt(shared.settings['prompt'])

    shared.gradio['interface_state'] = gr.State({k: None for k in shared.input_elements})
    shared.gradio['last_input'] = gr.State('')

    with gr.Tab('Text generation', elem_id='main'):
        with gr.Row():
            with gr.Column():
                shared.gradio['textbox'] = gr.Textbox(value=default_text, elem_classes=['textbox_default', 'add_scrollbar'], lines=27, label='Input')
                shared.gradio['max_new_tokens'] = gr.Slider(minimum=shared.settings['max_new_tokens_min'], maximum=shared.settings['max_new_tokens_max'], step=1, label='max_new_tokens', value=shared.settings['max_new_tokens'])
                with gr.Row():
                    shared.gradio['Generate'] = gr.Button('Generate', variant='primary')
                    shared.gradio['Stop'] = gr.Button('Stop', elem_id='stop')
                    shared.gradio['Continue'] = gr.Button('Continue')
                    shared.gradio['count_tokens'] = gr.Button('Count tokens')

                with gr.Row():
                    shared.gradio['prompt_menu'] = gr.Dropdown(choices=utils.get_available_prompts(), value='None', label='Prompt', elem_classes='slim-dropdown')
                    ui.create_refresh_button(shared.gradio['prompt_menu'], lambda: None, lambda: {'choices': utils.get_available_prompts()}, 'refresh-button')
                    shared.gradio['save_prompt'] = gr.Button('💾', elem_classes='refresh-button')
                    shared.gradio['delete_prompt'] = gr.Button('🗑️', elem_classes='refresh-button')

                shared.gradio['status'] = gr.Markdown('')

            with gr.Column():
                with gr.Tab('Raw'):
                    shared.gradio['output_textbox'] = gr.Textbox(lines=27, label='Output', elem_classes=['textbox_default_output', 'add_scrollbar'])

                with gr.Tab('Markdown'):
                    shared.gradio['markdown_render'] = gr.Button('Render')
                    shared.gradio['markdown'] = gr.Markdown()

                with gr.Tab('HTML'):
                    shared.gradio['html'] = gr.HTML()


def create_event_handlers():
    gen_events = []
    shared.input_params = gradio('textbox', 'interface_state')
    output_params = gradio('output_textbox', 'html')

    gen_events.append(shared.gradio['Generate'].click(
        lambda x: x, gradio('textbox'), gradio('last_input')).then(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        generate_reply_wrapper, shared.input_params, output_params, show_progress=False).then(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        lambda: None, None, None, _js=f'() => {{{ui.audio_notification_js}}}')
        # lambda: None, None, None, _js="() => {element = document.getElementsByTagName('textarea')[0]; element.scrollTop = element.scrollHeight}")
    )

    gen_events.append(shared.gradio['textbox'].submit(
        lambda x: x, gradio('textbox'), gradio('last_input')).then(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        generate_reply_wrapper, shared.input_params, output_params, show_progress=False).then(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        lambda: None, None, None, _js=f'() => {{{ui.audio_notification_js}}}')
        # lambda: None, None, None, _js="() => {element = document.getElementsByTagName('textarea')[0]; element.scrollTop = element.scrollHeight}")
    )

    shared.gradio['markdown_render'].click(lambda x: x, gradio('output_textbox'), gradio('markdown'), queue=False)
    gen_events.append(shared.gradio['Continue'].click(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        generate_reply_wrapper, [shared.gradio['output_textbox']] + shared.input_params[1:], output_params, show_progress=False).then(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        lambda: None, None, None, _js=f'() => {{{ui.audio_notification_js}}}')
        # lambda: None, None, None, _js="() => {element = document.getElementsByTagName('textarea')[1]; element.scrollTop = element.scrollHeight}")
    )

    shared.gradio['Stop'].click(stop_everything_event, None, None, queue=False, cancels=gen_events if shared.args.no_stream else None)
    shared.gradio['prompt_menu'].change(load_prompt, gradio('prompt_menu'), gradio('textbox'), show_progress=False)
    shared.gradio['save_prompt'].click(
        lambda x: x, gradio('textbox'), gradio('save_contents')).then(
        lambda: 'prompts/', None, gradio('save_root')).then(
        lambda: utils.current_time() + '.txt', None, gradio('save_filename')).then(
        lambda: gr.update(visible=True), None, gradio('file_saver'))

    shared.gradio['delete_prompt'].click(
        lambda: 'prompts/', None, gradio('delete_root')).then(
        lambda x: x + '.txt', gradio('prompt_menu'), gradio('delete_filename')).then(
        lambda: gr.update(visible=True), None, gradio('file_deleter'))

    shared.gradio['count_tokens'].click(count_tokens, gradio('textbox'), gradio('status'), show_progress=False)
