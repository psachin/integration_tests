# -*- coding: utf-8 -*-
from collections import OrderedDict

from cfme import web_ui as ui
from cfme.exceptions import TemplateNotFound
from cfme.fixtures import pytest_selenium as sel
from cfme.services import requests
from cfme.web_ui import AngularSelect, fill, flash, form_buttons, tabstrip, toolbar
from cfme.web_ui.menu import nav
from utils import version
from utils import normalize_text
from utils.log import logger
from utils.version import current_version
from utils.wait import wait_for

# nav imports
import cfme.infrastructure.virtual_machines  # NOQA


submit_button = form_buttons.FormButton("Submit")

template_select_form = ui.Form(
    fields=[
        ('template_table', ui.Table('//div[@id="pre_prov_div"]//table')),
        ('cancel_button', form_buttons.cancel)
    ]
)


def select_security_group(sg):
    """Workaround for select box that is immediately replaced by the same
       select box no matter what selenium clicks on (but works fine
       manually).  For now only selects one item even though it's a
       multiselect.

    """
    val = sel.get_attribute(
        "//select[@id='environment__security_groups']/option[normalize-space(.)='{}']".format(sg),
        'value')
    if current_version() < "5.4":
        sel.browser().execute_script(
            "$j('#environment__security_groups').val('%s');"
            "$j.ajax({type: 'POST', url: '/miq_request/prov_field_changed/new',"
            " data: {'environment__security_groups':'%s'}})" % (val, val))
    sel.wait_for_ajax()
    sel.sleep(1)

provisioning_form = tabstrip.TabStripForm(
    fields=[
        ('submit_button', form_buttons.FormButton("Submit")),
        ('submit_copy_button', form_buttons.FormButton("Submit this provisioning request")),
        ('cancel_button', form_buttons.cancel),
        ('host_submit_button', form_buttons.host_provision_submit),
        ('host_cancel_button', form_buttons.host_provision_cancel)
    ],
    tab_fields=OrderedDict([

        ('Request', [
            ('email', ui.Input('requester__owner_email')),
            ('first_name', ui.Input('requester__owner_first_name')),
            ('last_name', ui.Input('requester__owner_last_name')),
            ('notes', ui.Input('requester__request_notes')),
            ('manager_name', ui.Input('requester__owner_manager'))
        ]),

        ('Purpose', [
            ('apply_tags', ui.CheckboxTree('//div[@id="all_tags_treebox"]//ul'))
        ]),

        ('Catalog', [
            # Cloud
            ('num_instances', {
                version.LOWEST: ui.Select('select#service__number_of_vms'),
                '5.5': AngularSelect('service__number_of_vms')}),
            ('instance_name', '//input[@name="service__vm_name"]'),
            ('instance_description', ui.Input('service__vm_description')),

            # Infra
            ('vm_filter', {
                version.LOWEST: ui.Select('select#service__vm_filter'),
                '5.5': AngularSelect('service__vm_filter')}),
            ('num_vms', {
                version.LOWEST: ui.Select('select#service__number_of_vms'),
                '5.5': AngularSelect('service__number_of_vms')}),
            ('vm_name', '//input[@name="service__vm_name"]'),
            ('vm_description', ui.Input('service__vm_description')),
            ('catalog_name', ui.Table('//div[@id="prov_vm_div"]/table')),
            ('provision_type', {
                version.LOWEST: ui.Select('select#service__provision_type'),
                '5.5': AngularSelect('service__provision_type')}),
            ('linked_clone', ui.Input('service__linked_clone')),
            ('pxe_server', {
                version.LOWEST: ui.Select('select#service__pxe_server_id'),
                '5.5': AngularSelect('service__pxe_server_id')}),
            ('pxe_image', ui.Table('//div[@id="prov_pxe_img_div"]/table')),
            ('iso_file', ui.Table('//div[@id="prov_iso_img_div"]/table'))
        ]),

        ('Environment', [
            ('automatic_placement', ui.Input('environment__placement_auto')),

            # Cloud
            ('availability_zone', {
                version.LOWEST: ui.Select('select#environment__placement_availability_zone'),
                '5.5': AngularSelect('environment__placement_availability_zone')}),
            ('virtual_private_cloud', {
                version.LOWEST: ui.Select('select#environment__cloud_network'),
                '5.5': AngularSelect('environment__cloud_network')}),
            ('cloud_network', {
                version.LOWEST: ui.Select('select#environment__cloud_network'),
                '5.5': AngularSelect('environment__cloud_network')}),
            ('cloud_subnet', {
                version.LOWEST: ui.Select('select#environment__cloud_subnet'),
                '5.5': AngularSelect('environment__cloud_subnet')}),
            ('security_groups', {
                version.LOWEST: ui.Select('select#environment__security_groups'),
                '5.5': AngularSelect('environment__security_groups')}),
            ('resource_groups', {
                version.LOWEST: ui.Select('select#environment__resource_group'),
                '5.5': AngularSelect('environment__resource_group')}),
            ('public_ip_address', {
                version.LOWEST: ui.Select('select#environment__floating_ip_address'),
                '5.5': AngularSelect('environment__floating_ip_address')}),



            # Infra
            ('provider_name', {
                version.LOWEST: ui.Select('select#environment__placement_ems_name'),
                '5.5': AngularSelect('environment__placement_ems_name')}),
            ('datacenter', {
                version.LOWEST: ui.Select('select#environment__placement_dc_name'),
                '5.5': AngularSelect('environment__placement_dc_name')}),
            ('cluster', {
                version.LOWEST: ui.Select('select#environment__placement_cluster_name'),
                '5.5': AngularSelect('environment__placement_cluster_name')}),
            ('resource_pool', {
                version.LOWEST: ui.Select('select#environment__placement_rp_name'),
                '5.5': AngularSelect('environment__placement_rp_name')}),
            ('folder', {
                version.LOWEST: ui.Select('select#environment__placement_folder_name'),
                '5.5': AngularSelect('environment__placement_folder_name')}),
            ('host_filter', {
                version.LOWEST: ui.Select('select#environment__host_filter'),
                '5.5': AngularSelect('environment__host_filter')}),
            ('host_name', ui.Table('//div[@id="prov_host_div"]/table')),
            ('datastore_create', '#environment__new_datastore_create'),
            ('datastore_filter', {
                version.LOWEST: ui.Select('select#environment__ds_filter'),
                '5.5': AngularSelect('environment__ds_filter')}),
            ('datastore_name', ui.Table('//div[@id="prov_ds_div"]/table')),
        ]),
        ('Hardware', [
            ('num_sockets', {
                version.LOWEST: ui.Select('select#hardware__number_of_sockets'),
                '5.5': AngularSelect('hardware__number_of_sockets')}),
            ('cores_per_socket', {
                version.LOWEST: ui.Select('select#hardware__cores_per_socket'),
                '5.5': AngularSelect('hardware__cores_per_socket')}),
            ('num_cpus', AngularSelect('hardware__number_of_cpus')),
            ('memory', {
                version.LOWEST: ui.Select('select#hardware__vm_memory'),
                '5.5': AngularSelect('hardware__vm_memory')}),
            ('disk_format', ui.Radio('hardware__disk_format')),
            ('vm_limit_cpu', ui.Input('hardware__cpu_limit')),
            ('vm_limit_memory', ui.Input('hardware__memory_limit')),
            ('vm_reserve_cpu', ui.Input('hardware__cpu_reserve')),
            ('vm_reserve_memory', ui.Input('hardware__memory_reserve')),
        ]),

        # Infra
        ('Network', [
            ('vlan', {
                version.LOWEST: ui.Select('select#network__vlan'),
                '5.5': AngularSelect('network__vlan')}),
        ]),

        # Cloud
        ('Properties', [
            ('instance_type', {
                version.LOWEST: ui.Select('select#hardware__instance_type'),
                '5.5': AngularSelect('hardware__instance_type')}),
            ('guest_keypair', {
                version.LOWEST: ui.Select('select#hardware__guest_access_key_pair',
                none={'5.4': "<None>",
                      version.LOWEST: "<No Choices Available>"}),
                '5.5': AngularSelect('hardware__guest_access_key_pair',
                none={'5.4': "<None>",
                      version.LOWEST: "<No Choices Available>"})}),
            ('hardware_monitoring', {
                version.LOWEST: ui.Select('select#hardware__monitoring'),
                '5.5': AngularSelect('hardware__monitoring')}),
            ('boot_disk_size', AngularSelect('hardware__boot_disk_size')),
            # GCE
            ('is_preemtible', {version.LOWEST: None,
                              '5.7': ui.Input('hardware__is_preemptible')})
        ]),

        ('Customize', [
            # Common
            ('dns_servers', ui.Input('customize__dns_servers')),
            ('dns_suffixes', ui.Input('customize__dns_suffixes')),
            ('specification', {
                version.LOWEST: ui.Select('select#customize__sysprep_enabled'),
                '5.5': AngularSelect('customize__sysprep_enabled')}),
            ('customize_type', {
                version.LOWEST: ui.Select('select#customize__sysprep_enabled'),
                '5.5': AngularSelect('customize__sysprep_enabled')}),
            ('specification_name', ui.Table('//div[@id="prov_vc_div"]/table')),

            # Cloud
            ('computer_name', ui.Input('customize__linux_host_name')),
            ('domain_name', ui.Input('customize__linux_domain_name')),

            # Azure
            ('admin_username', ui.Input('customize__root_username')),
            ('admin_password', ui.Input('customize__root_password')),

            # Infra
            ('linux_host_name', ui.Input('customize__linux_host_name')),
            ('linux_domain_name', ui.Input('customize__linux_domain_name')),
            ('prov_host_name', ui.Input('customize__hostname')),
            ('ip_address', ui.Input('customize__ip_addr')),
            ('subnet_mask', ui.Input('customize__subnet_mask')),
            ('gateway', ui.Input('customize__gateway')),
            ('custom_template', ui.Table('//div[@id="prov_template_div"]/table')),
            ('root_password', ui.Input('customize__root_password')),
            ('vm_host_name', ui.Input('customize__hostname')),
        ]),
        ('Schedule', [
            # Common
            ('schedule_type', ui.Radio('schedule__schedule_type')),
            ('provision_date', ui.Calendar('miq_date_1')),
            ('provision_start_hour', {
                version.LOWEST: ui.Select('select#start_hour'),
                '5.5': AngularSelect('start_hour')}),
            ('provision_start_min', {
                version.LOWEST: ui.Select('select#start_min'),
                '5.5': AngularSelect('start_min')}),
            ('power_on', ui.Input('schedule__vm_auto_start')),
            ('retirement', {
                version.LOWEST: ui.Select('select#schedule__retirement'),
                '5.5': AngularSelect('schedule__retirement')}),
            ('retirement_warning', {
                version.LOWEST: ui.Select('select#schedule__retirement_warn'),
                '5.5': AngularSelect('schedule__retirement_warn')}),

            # Infra
            ('stateless', ui.Input('schedule__stateless')),
        ])
    ])
)


def generate_nav_function(tb_item):
    def f(context):
        # Here it also can have long spinners
        with sel.ajax_timeout(90):
            toolbar.select('Lifecycle', tb_item)
        provider = context['provider']
        template_name = context['template_name']
        template_select_form.template_table._update_cache()
        template = template_select_form.template_table.find_row_by_cells({
            'Name': template_name,
            'Provider': provider if isinstance(provider, basestring) else provider.name
        })
        if template:
            sel.click(template)
            # In order to mitigate the sometimes very long spinner timeout, raise the timeout
            with sel.ajax_timeout(90):
                sel.click(form_buttons.FormButton("Continue", force_click=True))

        else:
            raise TemplateNotFound('Unable to find template "{}" for provider "{}"'.format(
                template_name, provider.key))
    return f

nav.add_branch('infra_vm_and_templates', {
    'infrastructure_provision_vms': generate_nav_function("Provision VMs"),
})


def do_vm_provisioning(template_name, provider, vm_name, provisioning_data, request,
                       smtp_test, num_sec=1500, wait=True):
    # generate_tests makes sure these have values
    sel.force_navigate('infrastructure_provision_vms', context={
        'provider': provider,
        'template_name': template_name,
    })

    note = ('template {} to vm {} on provider {}'.format(template_name, vm_name, provider.key))
    provisioning_data.update({
        'email': 'template_provisioner@example.com',
        'first_name': 'Template',
        'last_name': 'Provisioner',
        'notes': note,
    })

    fill(provisioning_form, provisioning_data,
         action=provisioning_form.submit_button)
    flash.assert_no_errors()
    if not wait:
        return

    # Wait for the VM to appear on the provider backend before proceeding to ensure proper cleanup
    logger.info('Waiting for vm %s to appear on provider %s', vm_name, provider.key)
    wait_for(provider.mgmt.does_vm_exist, [vm_name], handle_exception=True, num_sec=600)

    # nav to requests page happens on successful provision
    logger.info('Waiting for cfme provision request for vm %s', vm_name)
    row_description = 'Provision from [{}] to [{}]'.format(template_name, vm_name)
    cells = {'Description': row_description}
    try:
        row, __ = wait_for(requests.wait_for_request, [cells],
                           fail_func=requests.reload, num_sec=num_sec, delay=20)
    except Exception as e:
        requests.debug_requests()
        raise e
    assert normalize_text(row.status.text) == 'ok' \
                                              and normalize_text(
        row.request_state.text) == 'finished'

    if smtp_test:
        # Wait for e-mails to appear
        def verify():
            if current_version() >= "5.4":
                approval = dict(subject_like="%%Your Virtual Machine configuration was Approved%%")
            else:
                approval = dict(text_like="%%Your Virtual Machine Request was approved%%")
            expected_text = "Your virtual machine request has Completed - VM:%%{}".format(vm_name)
            return (
                len(smtp_test.get_emails(**approval)) > 0 and
                len(smtp_test.get_emails(subject_like=expected_text)) > 0
            )

        wait_for(verify, message="email receive check", delay=5)


def copy_request(cells, modifications):
    with requests.copy_request(cells):
        fill(provisioning_form, modifications)


def copy_request_by_vm_and_template_name(vm_name, template_name, modifications, multi=False):
    multistr = "###" if multi else ""
    row_description = "Provision from [{}] to [{}{}]".format(template_name, vm_name, multistr)
    return copy_request({'Description': row_description}, modifications)


def go_to_request_by_vm_and_template_name(vm_name, template_name, multi=False):
    multistr = "###" if multi else ""
    row_description = "Provision from [{}] to [{}{}]".format(template_name, vm_name, multistr)
    return requests.go_to_request({'Description': row_description})
