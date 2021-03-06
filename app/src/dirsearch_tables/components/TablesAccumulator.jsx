import _ from 'lodash'
import React from 'react'

import { Heading } from 'grommet'

import ReactPaginate from '../../common/paginate/ReactPaginate.jsx'
import Search from '../../common/search/Search.jsx'
import DirsearchTable from './DirsearchTable.jsx'


class TablesAccumulator extends React.Component {
	constructor(props) {
		super(props);

		this.state = {
			pageCount: Math.ceil((this.props.selected.ips + this.props.selected.hosts) / this.props.pageSize)
		}
	}

	componentWillReceiveProps(nextProps) {
		this.setState({
			pageCount: Math.ceil((nextProps.selected.ips + nextProps.selected.hosts) / nextProps.pageSize)
		});
	}

	render() {
		const { ips, hosts, files, project_name, project_uuid, applyFilters, changePage, getFilesIps, getFilesHosts } = this.props;
		let tables = [];

		for (var each_ip of ips) {
			const files_for_ip = _.get(files.files.ip, each_ip.ip_id, {});
			const stats_for_ip = _.get(files.stats.ip, each_ip.ip_id, {});

			for (var each_port of each_ip.scans) {
				const files_for_ip_port = _.get(files_for_ip, each_port.port_number, []);
				const stats_for_ip_port = _.get(stats_for_ip, each_port.port_number, {});

				tables.push(
					<DirsearchTable key={each_ip.ip_id + "_" + each_port.scan_id} 
									target={each_ip.ip_address}
									target_id={each_ip.ip_id}
									port_number={each_port.port_number}
									files={files_for_ip_port}
									stats={stats_for_ip_port}
									project_uuid={project_uuid}
									requestMore={getFilesIps} />
				);
			}
		}

		for (var each_host of hosts) {
			const files_for_host = _.get(files.files.host, each_host.host_id, {});
			const stats_for_host = _.get(files.stats.host, each_host.host_id, {});

			let ports = new Set();

			for (var each_ip_address of each_host.ip_addresses) {				
				for (var each_port of each_ip_address.scans) {
					ports.add(each_port.port_number);
				}
			}

			for (var port_number of ports) {
				const files_for_host_port = _.get(files_for_host, port_number, []);
				const stats_for_host_port = _.get(stats_for_host, port_number, {});

				tables.push(
					<DirsearchTable
						key={each_host.host_id + "_" + port_number} 
						target={each_host.hostname}
						target_id={each_host.host_id}
						port_number={port_number}
						files={files_for_host_port}
						stats={stats_for_host_port}
						project_uuid={project_uuid}
						requestMore={getFilesHosts}
					/>
				);
			}
		}

		return (
			<div>
				<Heading level="2">{project_name}</Heading>
				<Search applyFilters={applyFilters} />
				<br />
				{tables}
				<ReactPaginate
					pageNumber={this.props.pageNumberUnmodified}
					pageCount={this.state.pageCount}
					clickHandler={changePage} />
			</div>
		)
	}
}

export default TablesAccumulator;
