import flet as ft
from pytubefix import YouTube
import concurrent.futures
import json


def main(page: ft.Page):
    page.title = 'YouTube Downloader'
    page.padding = 20
    page.scrollable = True

    thumbnail = ft.Container(width=576, height=320, image_fit=ft.ImageFit.COVER)
    title = ft.Text('', size=25, no_wrap=False, width=640, text_align=ft.CrossAxisAlignment.START)
    description = ft.Text('', size=15, no_wrap=False, width=640, height=170)
    legnth_views = ft.Text('', size=12)
    views = ft.Text('', size=12)

    user_link = ft.TextField(label='Video link',
                             hint_text='Please input youtube video link',
                             height=60, width=500)

    # create varibles for error dialog, title and message
    error_title = ft.Text('', size=20)
    error_message = ft.Text('', size=15)

    # create a function to close the dialog
    def close_error_dlg(e):
        dlg_modal.open = False
        user_link.value = ''
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
        # on_dismiss=lambda e: print("Modal dialog dismissed!"),
    )

    '''
    this function will be called from download_completed callback on startDownload fucntion
    and open a dialog modal to show the download completed message'''

    def download_completed(stream, file_handle):
        progrss.bgcolor = ft.colors.GREEN
        open_error_dlg_modal('Download completed', 'The video has been downloaded successfully.')

    '''#monitor the download progress'''

    def on_progress(stream, chunk, bytes_remaining):
        total_size = stream.filesize  # Assuming filesize is available
        downloaded = total_size - bytes_remaining
        percentage = f'{downloaded / total_size:.2f}'
        print(percentage)
        progrss.value = percentage
        page.update()

    '''
    create a function to start download with arg path 
    to save the video to selected path from file picker'''

    def startDownload(path):
        progrss.value = 0
        progrss.visible = True
        url = user_link.value
        try:
            yt = YouTube(url, on_progress_callback=on_progress, on_complete_callback=download_completed)
            video = yt.streams.first()  # Select the first stream
            open_error_dlg_modal('Downloading...', 'The video is downloading. Please wait...')
            video.download(output_path=path)

        except Exception as e:
            open_error_dlg_modal('Error', 'An error occurred while downloading the video.')

    direct_path = 'directory.json'
    selected_path = ft.Text('')

    # after user click choose on file picker button, this function will be called
    # to get the directorry result and save the selected path to json file

    def get_directory_result(e: ft.FilePickerResultEvent):
        selected_path.value = e.path if e.path else 'Cancelled!'
        try:
            with open(direct_path, 'r+') as json_file:
                json_data = json.load(json_file)
                json_data["selected_path"] = selected_path.value
                json_file.seek(0)
                json.dump(json_data, json_file, indent=4)

                #close the directory json file
                json_file.close()

        except (IOError, json.JSONDecodeError) as e:
            print(f"Error processing JSON file: {e}")

    # create a file picker to select the directory to save the video
    # and add to page as overlay

    file_picker = ft.FilePicker(on_result=get_directory_result, )
    page.overlay.append(file_picker)
    page.update()

    # check if the selected path is already saved in json file
    # if not, open the file picker to select the directory
    # if yes, start download the video

    def check_save_directory(direct_path):
        try:
            with open(direct_path, 'r+') as json_file:
                # Load the JSON data
                json_data = json.load(json_file)

                if not json_data.get("selected_path"):

                    # open the filck picker to select the directory
                    file_picker.get_directory_path()
                else:
                    '''path = json_data.get("selected_path")'''
                    path = json_data.get("selected_path")

                    # start download the video with path as argument
                    startDownload(path)

                #close the directory json file
                json_file.close()

        except (IOError, json.JSONDecodeError) as e:
            print(f"Error processing JSON file: {e}")

    # line separator
    devider = ft.Divider(visible=False)

    # download button to start download the video
    # when user click the download button, it will call check_save_directory function
    download_btn = ft.ElevatedButton('Download',
                                     width=180,
                                     height=50,
                                     visible=False,
                                     bgcolor=ft.colors.PRIMARY_CONTAINER,
                                     icon='download',
                                     on_click=lambda e: check_save_directory(direct_path))

    # progress bar to show the download progress
    progrss = ft.ProgressBar(value=0, height=10, width=400, visible=False, border_radius=5)

    # chips to show the video length and views
    chips_legnth_views = ft.Chip(label=legnth_views,
                                 leading=ft.Icon(ft.icons.TIMELAPSE),
                                 bgcolor=ft.colors.PRIMARY_CONTAINER,
                                 visible=False)

    chips_views = ft.Chip(label=views,
                          leading=ft.Icon(ft.icons.VIEW_AGENDA),
                          bgcolor=ft.colors.PRIMARY_CONTAINER,
                          visible=False)

    '''
    #get video title, thumbnail, description and resolution'''

    def get_title(yt):
        try:
            title.value = yt.title
        except Exception as e:
            print('Unable to get video title')

    def get_thumnail(yt):
        try:
            thumbnail.image_src = yt.thumbnail_url
        except Exception as e:
            print('Unable to get video thumbnail')

    def get_description(yt):
        try:
            streams = yt.streams
            description.value = yt.description
        except Exception as e:
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
            print(remove_p_from_resolutions)
        except Exception as e:
            description.value = 'Unable to get video resolution'

    # check if the link is valid or not
    def check_link():
        url = user_link.value
        try:
            yt = YouTube(url)
            return True
        except Exception as e:
            return False

    # get video info, when called, it will check the link is valid or not
    # if valid, it will get the video title, thumbnail, description and resolution
    def get_video_info(e):
        open_error_dlg_modal('Searching...', 'Video information will be loaded once searching is completed')
        url = user_link.value
        if not check_link():
            open_error_dlg_modal('Error', 'Invalid YouTube video link')
            return
        else:
            yt = YouTube(url)
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.submit(get_title, yt)
                executor.submit(get_thumnail, yt)
                executor.submit(get_description, yt)
                executor.submit(get_resolution, yt)

        legnth_views.value = f' {yt.length / 60:,.2f} mins '
        views.value = f' {yt.views:,.0f} views '

        devider.visible = True
        download_btn.visible = True
        chips_legnth_views.visible = True
        chips_views.visible = True

        close_error_dlg(e)
        page.update()

    # add all the field to the page
    page.add(
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
                              icon='search',
                              width=150,
                              height=60,
                              bgcolor=ft.colors.PRIMARY_CONTAINER)
        ], alignment=ft.MainAxisAlignment.CENTER, ),

        ft.Divider(),

        ft.Row([
            ft.Column([thumbnail]),

            ft.Column([

                ft.Row([
                    title,
                ], height=65),

                ft.Row([
                    ft.Text('', height=10),
                ]),

                ft.Row([
                    description
                ]),

                ft.Row([
                    ft.Text('', height=5),
                ]),

                ft.Row([
                    ft.Column([
                        chips_legnth_views
                    ]),
                    ft.Column([
                        chips_views
                    ])
                ]),
            ], height=320)
        ]),
        devider,
        ft.Row([
            download_btn
        ], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([progrss], alignment=ft.MainAxisAlignment.CENTER),

    )


ft.app(main)
