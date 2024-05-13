import flet as ft
from flet_core import ProgressBar
from pytubefix import YouTube, exceptions
import concurrent.futures
import json


def main(page: ft.Page):
    page.title = 'YouTube Downloader'
    page.window_maximized = True
    page.padding = 20
    page.scrollable = True

    half = page.window_width / 2
    thumbnail_height = half / (16 / 9)

    thumbnail = ft.Container(width=half, height=thumbnail_height, image_fit=ft.ImageFit.COVER)
    title = ft.Text('', size=20, width=half, max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS)
    description = ft.Text('', size=15, no_wrap=False, width=half,
                          max_lines=5,
                          overflow=ft.TextOverflow.ELLIPSIS, height=120)
    length_views = ft.Text('', size=12)
    views = ft.Text('', size=12)
    author = ft.Text('', size=12, weight=ft.FontWeight.BOLD)

    user_link = ft.TextField(label='Video link',
                             hint_text='Please input youtube video link',
                             height=60, width=500)

    # create variables for error dialog, title and message
    error_title = ft.Text('', size=20)
    error_message = ft.Text('', size=15)

    res_selected = ft.Text('')
    download_option_label = ft.Text('Download option', size=15, visible=False)

    divider_1 = ft.Divider(visible=False)

    def dropdown_change(e):
        res_selected.value = resolution_list.value
        page.update()
        print(res_selected.value)

    resolution_list = ft.Dropdown(
        on_change=dropdown_change,
        hint_text='Choose resolutions: ',
        visible=False
    )

    # create a function to close the dialog
    def close_error_dlg(e):
        dlg_modal.open = False
        user_link.focus()
        page.update()

    # create a function to open the dialog
    def open_error_dlg_modal(title, message):
        error_title.value = title
        error_message.value = message
        page.dialog = dlg_modal
        dlg_modal.open = True
        page.update()

    # create a dialog modal to display error message
    dlg_modal = ft.AlertDialog(
        modal=True,
        title=error_title,
        content=error_message,
        actions=[
            ft.TextButton("OK", on_click=close_error_dlg, width=100, height=40),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    '''
    this function will be called from download_completed callback on start_download function
    and open a dialog modal to show the download completed message'''

    def download_completed(stream, file_handle):
        progress.bgcolor = ft.colors.GREEN
        open_error_dlg_modal('Download completed', 'The video has been downloaded successfully.')

    def on_progress(stream, chunk, bytes_remaining):
        total_size = stream.filesize  # Assuming file size is available
        downloaded = total_size - bytes_remaining
        percentage = f'{downloaded / total_size:.2f}'
        print(percentage)
        progress.value = percentage
        page.update()

    '''
    create a function to start download with arg path 
    to save the video to selected path from file picker'''

    def start_download(path):
        url = user_link.value
        progress.value = 0
        progress.visible = True
        try:
            yt = YouTube(url, on_progress_callback=on_progress, on_complete_callback=download_completed)

            #download specific resolution
            video = yt.streams.filter(res=str(res_selected.value)).first()

            open_error_dlg_modal('Downloading...', 'The video is downloading. Please wait...')
            video.download(output_path=path, )

        except exceptions:
            open_error_dlg_modal('Error', 'An error occurred while downloading the video.')

    direct_path = 'directory.json'
    selected_path = ft.Text('')

    # after user click choose on file picker button, this function will be called
    # to get the directory result and save the selected path to json file

    def get_directory_result(e: ft.FilePickerResultEvent):
        if e.path:
            selected_path.value = e.path
            save_selected_path('selected_path', selected_path.value)

    # create a file picker to select the directory to save the video
    # and add to page as overlay

    file_picker = ft.FilePicker(on_result=get_directory_result, )
    page.overlay.append(file_picker)
    page.update()

    # check if the selected path is already saved in json file
    # if not, open the file picker to select the directory
    # if yes, start download the video

    def save_selected_path(value, data):
        try:
            with open(direct_path, 'r+') as json_file:
                json_data = json.load(json_file)
                json_data[value] = data
                json_file.seek(0)
                json.dump(json_data, json_file, indent=4)

        except (IOError, json.JSONDecodeError) as e:
            print(f"Error processing JSON file: {e}")

    def check_save_path():
        try:
            with open(direct_path, 'r+') as json_file:
                # Load the JSON data
                json_data = json.load(json_file)

                if not json_data.get("selected_path"):
                    return False
                else:
                    '''path = json_data.get("selected_path")'''
                    return json_data.get("selected_path")
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error processing JSON file: {e}")

    def check_save_directory():
        selected_directory = check_save_path()
        if not selected_directory:
            file_picker.get_directory_path()
        else:
            start_download(selected_directory)

    # line separator
    divider = ft.Divider(visible=False)

    # download button to start download the video
    # when user click the download button, it will call check_save_directory function
    download_btn = ft.ElevatedButton('Download',
                                     width=180,
                                     height=50,
                                     visible=False,
                                     bgcolor=ft.colors.PRIMARY_CONTAINER,
                                     icon=ft.icons.DOWNLOAD,
                                     on_click=lambda e: check_save_directory())

    def close_setting_dlg():
        dlg_setting_modal.open = False
        user_link.focus()
        page.update()

    # create a function to open the dialog
    def open_setting_dlg_modal(title, message):
        error_title.value = title
        error_message.value = message
        page.dialog = dlg_setting_modal
        dlg_setting_modal.open = True
        page.update()

    def on_change_button_click():
        file_picker.get_directory_path()
        close_setting_dlg()

    # create a dialog modal to display error message
    dlg_setting_modal = ft.AlertDialog(
        modal=True,
        title=error_title,
        content=error_message,
        actions=[
            ft.TextButton('Change', on_click=lambda _: on_change_button_click(), width=80, height=40),
            ft.TextButton("OK", on_click=lambda _: close_setting_dlg(), width=80, height=40),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def download_location_clicked():
        if not check_save_path():
            text = "None"
        else:
            text = check_save_path()
        open_setting_dlg_modal("Change directory", f'Your save directory is: {text}')

    setting_list = ft.PopupMenuButton(
        icon=ft.icons.SETTINGS,
        items=[
            ft.PopupMenuItem(icon=ft.icons.EDIT_NOTE,
                             text="Download location",
                             on_click=lambda _: download_location_clicked()),
        ]
    )

    # progress bar to show the download progress
    progress: ProgressBar = ft.ProgressBar(value=0, height=5, width=400, visible=False, border_radius=5)

    def chip_clicked():
        return None

    # chips to show the video length and views
    chips_length_views = ft.Chip(label=length_views,
                                 leading=ft.Icon(ft.icons.TIMELAPSE),
                                 bgcolor=ft.colors.PRIMARY_CONTAINER,
                                 visible=False,
                                 on_click=lambda _: chip_clicked)

    chips_views = ft.Chip(label=views,
                          leading=ft.Icon(ft.icons.VIEW_AGENDA),
                          bgcolor=ft.colors.PRIMARY_CONTAINER,
                          visible=False,
                          on_click=lambda _: chip_clicked)

    chip_author = ft.Chip(label=author,
                          leading=ft.Icon(ft.icons.PERSON),
                          bgcolor=ft.colors.PRIMARY_CONTAINER,
                          visible=False,
                          on_click=lambda _: chip_clicked)

    def get_channel_name(yt):
        try:
            author.value = yt.author
        except Exception:
            print('Unable to get video title')

    def get_title(yt):
        try:
            title.value = yt.title
        except Exception:
            print('Unable to get video title')

    def get_thumbnail(yt):
        try:
            thumbnail.image_src = yt.thumbnail_url
        except Exception:
            print('Unable to get video thumbnail')

    def get_description(yt):
        try:
            streams = yt.streams
            description.value = yt.description
        except Exception:
            print('Unable to get video description')

    def get_resolution(yt):
        try:
            streams = yt.streams
            resolutions = []
            for stream in streams:
                resolution = stream.resolution
                if resolution not in resolutions:
                    resolutions.append(resolution)
            # remove None from the list and sort the list
            remove_p_from_resolutions = list(filter(None, resolutions))
            remove_p_from_resolutions.sort()
        except Exception:
            description.value = 'Unable to get video resolution'
        return remove_p_from_resolutions

    # check if the link is valid or not
    def check_link(url):
        try:
            yt = YouTube(url)
            return True
        except Exception:
            return False

    def show_res_dropdown():
        url = user_link.value
        yt = YouTube(url)
        res = get_resolution(yt)
        resolution_list.options = [
            ft.dropdown.Option(i) for i in res
        ]
        page.update()

    # get video info, when called, it will check the link is valid or not
    # if valid, it will get the video title, thumbnail, description and resolution
    def get_video_info(e):
        progress.visible = False
        open_error_dlg_modal('Searching...', 'Please wait while searching')
        url = user_link.value
        if not check_link(url):
            open_error_dlg_modal('Error', 'Invalid YouTube video link')
        else:
            yt = YouTube(url)
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.submit(get_title, yt)
                executor.submit(get_thumbnail, yt)
                executor.submit(get_description, yt)
                executor.submit(get_resolution, yt)
                executor.submit(get_channel_name, yt)

        length_views.value = f' {yt.length / 60:,.2f} min '
        views.value = f' {yt.views:,.0f} views '

        show_res_dropdown()
        divider.visible = True
        download_btn.visible = True
        chips_length_views.visible = True
        chips_views.visible = True
        chip_author.visible = True

        divider_1.visible = True
        resolution_list.visible = True
        download_option_label.visible = True

        close_error_dlg(e)
        page.update()

    # add all the field to the page
    page.add(
        setting_list,
        ft.Row([
            ft.Text('', size=30, height=30),
        ], alignment=ft.MainAxisAlignment.CENTER, ),

        ft.Row([
            ft.Text('YouTube Downloader', size=30),
        ], alignment=ft.MainAxisAlignment.CENTER),

        ft.Row([
            ft.Text('', size=30, height=30),
        ], alignment=ft.MainAxisAlignment.CENTER, ),

        ft.Row([
            user_link,
            ft.ElevatedButton('Search',
                              on_click=get_video_info,
                              icon=ft.icons.SEARCH,
                              width=150,
                              height=60,
                              bgcolor=ft.colors.PRIMARY_CONTAINER)
        ], alignment=ft.MainAxisAlignment.CENTER, ),

        ft.Divider(),

        ft.Row([
            ft.Column([thumbnail], expand=True, height=thumbnail_height),

            ft.Column([

                ft.Row([
                    title,
                ]),

                ft.Row([
                    ft.Column([
                        chip_author
                    ]),
                    ft.Column([
                        chips_length_views
                    ]),
                    ft.Column([
                        chips_views
                    ])
                ]),

                ft.Row([
                    ft.Text('', height=10),
                ]),

                ft.Row([
                    description
                ]),

                divider_1,
                ft.Row([
                    ft.Text('', height=10),
                ]),
                ft.Row([
                    download_option_label
                ]),
                ft.Row([
                    resolution_list
                ]),

            ], expand=True, height=thumbnail_height)
        ]),
        divider,
        ft.Row([
            download_btn
        ], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([progress], alignment=ft.MainAxisAlignment.CENTER),

    )


ft.app(main)
