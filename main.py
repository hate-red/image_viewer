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


    def on_window_resize(e) -> None:
        """
        Changes window inner elements sizes when window is resized
        """
        nonlocal main_row_height
        main_row_height = page.window.height - (menu_row_height + tools_row_height) # type: ignore

        page.update()


    async def keyboard_handler(e: ft.KeyboardEvent) -> None:
        match (e.key):
            case 'F':
                _ = await handle_pick_images(e) # type: ignore
            case 'D':
                _ = await handle_pick_dir(e) # type: ignore
            
            case 'Arrow Right': 
                swipe_right(e)
            case 'Arrow Left': 
                swipe_left(e)

            case 'E':
                apply_left_rotation(e)
            case 'R': 
                apply_right_rotation(e)
            case 'C':
                toggle_cropper_visibility(e)

            case 'Enter': 
                crop_image()

    def toggle_visibility() -> None:
        """
        Used in file pickers event handlers. 
        Make new elements visible when image/images are selected 
        """
        swipe_left_btn.visible = True if len(selected_images_paths) > 1 else False
        swipe_right_btn.visible = True if len(selected_images_paths) > 1 else False

        image_container.visible = True
        image_block.visible = True
        tools_row.visible = True
        selected_images_paths_text.visible = False

        save_file_btn.disabled = False


    def convert_to_b64(image: Image.Image) -> str:
        """
        Takes `pillow` Image object, saves it to RAM buffer,
        encodes is to `base64` string and decodes it into utf-8 string.
        This is highlt inefficient and is to be reworked in future
        """
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        
        base64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return base64_str


    def set_image_to_container(image: Image.Image) -> None:
        """
        Takes `pillow` Image, converts it to base64 string.
        That string to then put to `image_container` and displayed
        """
        base64_img = convert_to_b64(image)        
        
        image_container.src = base64_img
        page.update()


    def update_current_image(image: Image.Image | None = None) -> None:
        """
        Sets `current_image` and its index in `selected_images_paths`
        """
        nonlocal current_image, current_image_ind
        
        if image is None:
            current_image = Image.open(selected_images_paths[0]) # type: ignore
            current_image_ind = 0
        else:
            current_image = image

        set_image_to_container(current_image)


    async def handle_pick_dir(e) -> None:
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

        nonlocal selected_images_paths
        selected_images_paths = [
            path for path in Path(selected_dir).iterdir()
            if path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp'] 
        ]

        update_current_image()
        toggle_visibility()

        page.update()


    async def handle_pick_images(e) -> None:
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
        
        nonlocal selected_images_paths
        selected_images_paths = [image.path for image in images]

        update_current_image()
        toggle_visibility()

        page.update()


    def apply_left_rotation(e) -> None:
        """
        Event handler for rotating `current_image` left
        """
        nonlocal current_image

        if not current_image:
            return 
        
        current_image = current_image.rotate(90, expand=True)
        set_image_to_container(current_image)


    def apply_right_rotation(e) -> None:
        """
        Event handler for rotating `current_image` right
        """
        nonlocal current_image

        if not current_image:
            return 
        
        current_image = current_image.rotate(-90, expand=True)
        set_image_to_container(current_image)


    def swipe_left(e) -> None:
        """
        Event handler for switching to the previous image in the `selected_images_paths` list
        """
        nonlocal current_image, current_image_ind

        if current_image_ind <= 0:
            current_image_ind = len(selected_images_paths) - 1
        else:
            current_image_ind -= 1

        current_image = Image.open(selected_images_paths[current_image_ind]) # type: ignore
        set_image_to_container(current_image)


    def swipe_right(e) -> None:
        """
        Event handler for switching to the next image in the `selected_images_paths` list
        """
        nonlocal current_image, current_image_ind

        if current_image_ind >= len(selected_images_paths) - 1:
            current_image_ind = 0
        else:
            current_image_ind += 1

        current_image = Image.open(selected_images_paths[current_image_ind]) # type: ignore
        set_image_to_container(current_image)


    async def resize_crop_area(e: ft.DragUpdateEvent) -> None:
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

        e.control.update()


    async def change_cropper_position(e: ft.DragUpdateEvent) -> None:
        """
        Event handler for moving `cropper` with mouse
        """
        if e.local_delta.x is None or e.control.top is None: # type: ignore
            e.local_delta.x = 0 # type: ignore
            e.local_delta.y = 0 # type: ignore
            e.control.left = e.local_position.x
            e.control.top = e.local_position.y

        e.control.left = e.control.left + e.local_delta.x # type: ignore
        e.control.top = e.control.top + e.local_delta.y # type: ignore

        cropper.update()


    def toggle_cropper_visibility(e) -> None:
        """
        Toggles visibility of `crop_gesture_decector` and 
        its component `cropper` when `crop_btn` is pressed
        """
        cropper.visible = not cropper.visible
        crop_gesture_decector.visible = not crop_gesture_decector.visible

        cropper.update()


    def crop_image() -> None:
        top, left = cropper.top, cropper.left
        right, bottom = left + crop_area.width, top + crop_area.height # type: ignore

        cropped_image = current_image.crop((left, top, right, bottom)) #type: ignore
        set_image_to_container(cropped_image)
        crop_gesture_decector.visible = not crop_gesture_decector.visible

        page.update()


    # all the buttons for menu
    open_file_btn = ft.Button(
        content=ft.Text('Open Image', size=18), 
        on_click=handle_pick_images,
        height=40,
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
    selected_images_paths_text = ft.Text(
        value='No files selected', 
        size=24, 
        opacity=0.5
    )
    
    # a sort of overlay on current image
    # displaying area that would be cropped 
    crop_area = ft.Container(
        border=ft.Border.all(1, color=ft.Colors.BLUE_GREY_700),
        bgcolor=ft.Colors.BLUE_GREY_700,
        opacity=0.3,
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
                right=ft.BorderSide(4, ft.Colors.BLUE_GREY_700), 
                bottom=ft.BorderSide(4, ft.Colors.BLUE_GREY_700)
            )
        ),
        bottom=0,
        right=0,
    )
    # area to be cropped with control stacked on it
    cropper = ft.Stack([crop_area, resize_handle], visible=False)
    # realises crop tool functionality 
    crop_gesture_decector = ft.GestureDetector(
        drag_interval=10,
        mouse_cursor=ft.MouseCursor.MOVE,
        on_pan_update=change_cropper_position,
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
    
    # list of all images in a given directory
    selected_images_paths = []
    # storing image that is displayed right now
    current_image: Image.Image | None = None
    # index of current image in selected_images_paths
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
    crop_btn = ft.IconButton(ft.Icons.CROP, on_click=toggle_cropper_visibility)

    # collecting all elements into rows
    menu_row = ft.Row(
        controls=[open_file_btn, open_dir_btn, save_file_btn], 
        alignment=ft.MainAxisAlignment.CENTER,
    )

    # row where images are displayed
    main_row = ft.Row(
        controls=[
            ft.Column(
                controls=[swipe_left_btn], 
            ),
            selected_images_paths_text, 
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

    # designing page structure
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
    page.on_keyboard_event = keyboard_handler
    page.update()


if __name__ == "__main__":
    ft.run(main=main)
