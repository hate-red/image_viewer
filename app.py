import flet as ft

import io
import base64
from PIL import Image

from pathlib import Path
from dotenv import load_dotenv
from os import getenv


def configure_app(page: ft.Page) -> None:
    """
    Sets basic window configuration 
    """

    page.theme_mode = ft.ThemeMode.DARK

    page.expand = True
    page.title = 'Image Viewer'

    load_dotenv()


def main(page: ft.Page) -> None:
    configure_app(page)

    menu_row_height = 50
    tools_row_height = 50
    main_row_height = page.window.height - (menu_row_height + tools_row_height) # type: ignore


    def on_window_resize(e):
        """
        Changes window inner elements sizes when window is resized
        """
        nonlocal main_row_height
        main_row_height = page.window.height - (menu_row_height + tools_row_height) # type: ignore

        page.update()


    def toggle_visibility() -> None:
        """
        Used in file pickers event handlers. 
        Make new elements visible when image/images are selected 
        """
        image_container.visible = True
        image_block.visible = True
        tools_row.visible = True
        selected_images_text.visible = False
        save_file_btn.disabled = False


    def process_images_paths(images_paths: list) -> None:
        """
        Receives list of images paths and opens then as pillow `Image` objects 
        """
        if len(images_paths) > 1:
            swipe_left_btn.visible = True
            swipe_right_btn.visible = True

        nonlocal selected_images, current_image
        selected_images = [Image.open(path) for path in images_paths] # type: ignore
        current_image = selected_images[0]
        image_container.src = convert_to_b64(current_image)


    async def handle_pick_dir(e: ft.Event[ft.Button]) -> None:
        """
        Event handler for selecting directory with images. 
        Updates current image and displays new elements on the page 
        (image block itself, tools, swipe buttons)
        """
        
        path_or_none = getenv('INITIAL_DIR')
        initial_dir = Path(path_or_none) if path_or_none is not None else None 

        selected_dir = await ft.FilePicker().get_directory_path(
            dialog_title='Select dir',
            initial_directory=initial_dir.__str__()
        )

        if not selected_dir:
            return 

        dir = Path(selected_dir)
        images_paths = [
            path for path in dir.iterdir()
            if path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp'] 
        ]

        process_images_paths(images_paths)
        toggle_visibility()

        page.update()


    async def handle_pick_file(e: ft.Event[ft.Button]) -> None:
        """
        Event handler for selecting image file. 
        Updates current image and displays new elements on the page 
        (image block itself, tools)
        """
        images = await ft.FilePicker().pick_files(
            dialog_title='Select image',
            allow_multiple=True,
            allowed_extensions=['jpg', 'jpeg', 'png', 'webp'],
        )
        if not images:
            return
        
        images_paths = [image.path for image in images]

        process_images_paths(images_paths)
        toggle_visibility()

        page.update()


    def convert_to_b64(image: Image.Image):
        """
        Takes `pillow` Image object, saves it to RAM buffer,
        encodes is to `base64` string and decodes it into utf-8 string.
        This is highlt inefficient and is to be reworked in future
        """
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        
        base64_img = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return base64_img


    def update_image(image: Image.Image) -> None:
        """
        Takes `pillow` Image, converts it to base64 string.
        That string to then put to `image_container`
        """
        base64_img = convert_to_b64(image)        
        
        image_container.src = base64_img
        page.update()


    def apply_left_rotation(e) -> None:
        """
        Event handler for rotating `current_image` left
        """
        nonlocal current_image

        if not current_image:
            return 
        
        current_image = current_image.rotate(90, expand=True)
        update_image(current_image)


    def apply_right_rotation(e) -> None:
        """
        Event handler for rotating `current_image` right
        """
        nonlocal current_image

        if not current_image:
            return 
        
        current_image = current_image.rotate(-90, expand=True)
        update_image(current_image)


    def swipe_left(e):
        """
        Event handler for switching to the previous image in the `selected_images` list
        """
        nonlocal current_image, current_image_ind

        if current_image_ind <= 0:
            return

        current_image = selected_images[current_image_ind - 1]
        current_image_ind -= 1
        update_image(current_image)


    def swipe_right(e):
        """
        Event handler for switching to the next image in the `selected_images` list
        """
        nonlocal current_image, current_image_ind

        if current_image_ind >= len(selected_images) - 1:
            return

        current_image = selected_images[current_image_ind + 1]
        current_image_ind += 1
        update_image(current_image)


    def resize_crop_area(e: ft.DragUpdateEvent):
        """
        Event handler for resizing `crop_area` with mouse
        """
        if e.local_delta.x is None or e.control.width is None: # type: ignore
            e.local_delta.x = 0  # type: ignore
            e.local_delta.y = 0  # type: ignore
            e.control.width = resize_handle_size
            e.control.height = resize_handle_size

        crop_area.width = crop_area.width + e.local_delta.x # type: ignore
        crop_area.height = crop_area.height + e.local_delta.y # type: ignore

        page.update()


    def change_crop_area_position(e: ft.DragUpdateEvent):
        """
        Event handler for moving `crop_area` with mouse
        """
        if e.local_delta.x is None or e.control.top is None: # type: ignore
            e.local_delta.x = 0 # type: ignore
            e.local_delta.y = 0 # type: ignore
            e.control.left = e.local_position.x
            e.control.top = e.local_position.y

        e.control.left = e.control.left + e.local_delta.x # type: ignore
        e.control.top = e.control.top + e.local_delta.y # type: ignore

        page.update()


    def toggle_crop_area_visibility(e):
        """
        Toggles visibility of `crop_area` when `crop_btn` is pressed
        """
        cropper.visible = not cropper.visible
        crop_gesture_decector.visible = not crop_gesture_decector.visible

        page.update()


    # all the buttons for menu
    open_file_btn = ft.Button(
        content=ft.Text('Open Image', size=18), 
        on_click=handle_pick_file,
        height=40,
        autofocus=True,
    )
    open_dir_btn = ft.Button(
        content=ft.Text('Open Dir', size=18),
        on_click=handle_pick_dir,
        height=40,
    )
    save_file_btn = ft.Button(
        content=ft.Text('Save Image', size=18), 
        disabled=True,
        height=40,
    )

    # displays on startup when no images are selected
    selected_images_text = ft.Text(
        value='No files selected', 
        size=24, 
        opacity=0.5
    )
    
    # a sort of overlay on current image
    # displaying area that would be cropped 
    crop_area = ft.Container(
        border=ft.Border.all(1, color=ft.Colors.WHITE),
        width=300,
        height=300,
        expand=True,
    )

    resize_handle_size = 20

    # small handle in the bottom right corner 
    # of the crop_area to resize it
    resize_handle = ft.GestureDetector(
        on_pan_update=resize_crop_area,
        content=ft.Container(
            width=resize_handle_size,
            height=resize_handle_size,
            border=ft.Border(
                right=ft.BorderSide(4, ft.Colors.WHITE), 
                bottom=ft.BorderSide(4, ft.Colors.WHITE)
            )
        ),
        bottom=0,
        right=0,
    )
    cropper = ft.Stack([crop_area, resize_handle], visible=False)

    # realises crop tool functionality 
    crop_gesture_decector = ft.GestureDetector(
        drag_interval=10,
        mouse_cursor=ft.MouseCursor.MOVE,
        on_pan_update=change_crop_area_position,
        visible=False,
        content=cropper,
    )
    image_container = ft.Image(
        src='',
        visible=False,
        fit=ft.BoxFit.CONTAIN,
    )
    image_block =  ft.Stack(
        [image_container, crop_gesture_decector], 
        visible=False,
    )
    
    # storing image that is displayed right now
    current_image = None
    
    # list of all images in a given directory
    selected_images = []

    # index of current image in selected_images
    current_image_ind = 0

    # buttons to switch between images
    swipe_left_btn = ft.IconButton(
        ft.Icons.KEYBOARD_ARROW_LEFT_OUTLINED, 
        on_click=swipe_left,
        icon_size=50, 
        opacity=0.5,
        visible=False,
        height=main_row_height,
        expand=True,
    )
    swipe_right_btn = ft.IconButton(
        ft.Icons.KEYBOARD_ARROW_RIGHT_OUTLINED,
        on_click=swipe_right, 
        icon_size=50, 
        opacity=0.5,
        visible=False,
        height=main_row_height,
        expand=True,
    )

    # button resbonsible for creating crop_area over current_image
    crop_btn = ft.IconButton(ft.Icons.CROP, on_click=toggle_crop_area_visibility)

    # Collecting all elements into rows
    menu_row = ft.Row(
        controls=[open_file_btn, open_dir_btn, save_file_btn], 
        alignment=ft.MainAxisAlignment.CENTER,
    )

    main_row = ft.Row(
        controls=[
            ft.Column(
                controls=[swipe_left_btn], 
            ),
            selected_images_text, 
            image_block,
            ft.Column(
                controls=[swipe_right_btn], 
            ),
        ], 
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    tools_row = ft.Row(
        controls=[
            ft.IconButton(ft.Icons.ROTATE_LEFT, on_click=apply_left_rotation),
            crop_btn,
            ft.IconButton(ft.Icons.ROTATE_RIGHT, on_click=apply_right_rotation),
        ],
        alignment=ft.MainAxisAlignment.CENTER, 
        visible=False,
    )

    # Designing page structure
    page.add(
        ft.Container(
            content=menu_row,
            alignment=ft.Alignment.TOP_CENTER,
            height=menu_row_height,
        ),
        ft.Container(
            content=main_row,
            alignment=ft.Alignment.CENTER,
            height=main_row_height,
            expand=True
        ),
        ft.Container(
            content=tools_row,
            alignment=ft.Alignment.BOTTOM_CENTER,
            height=tools_row_height
        ),
    )

    # setting event handler for window resize
    page.on_resize = on_window_resize

    page.update()


if __name__ == "__main__":
    ft.run(main=main)
