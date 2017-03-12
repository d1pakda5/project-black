import _ from 'lodash';
import Reflux from 'reflux';

import ProjectActions from './ProjectActions.js';
import ProjectManager from '../common/ProjectManager.js';


class ProjectStore extends Reflux.Store
{
    constructor()
    {
        super();
        this.state = {
            "projects" : [],
            "loading": false,
            "errorMessage": null
        };

        // Create project manage
        this.projectManager = new ProjectManager();

        // Obtain the data and redraw the table
        this.projectManager.initialize(this.initializeProjects.bind(this));

        this.listenables = ProjectActions;

    }

    initializeProjects(projects) {
        this.loading("", false);

        this.setState({
            projects: projects
        });
        this.trigger(this.state);
    }

    loading(errorMessage, status) {
        // Make a mark that loading status = 'status'
        this.setState({
            errorMessage: errorMessage, 
            loading: status
        });

        this.trigger(this.state);        
    }

    onCreate(project_name)
    {
        this.loading("", true);

        this.projectManager.createProject(project_name, (result) => {
            if (result['status'] == 'success') {
                this.setState({
                    projects: this.projectManager.getProjects()
                });

                this.loading("", false);
            }
            else {
                this.loading(result['text'], false);                
            }
        });
    }

    onDelete(project_uuid)
    {
        this.loading("", true);
        console.log('deleting');
        this.projectManager.deleteProject(project_uuid, (result) => {
            if (result['status'] == 'success') {
                this.setState({
                    projects: this.projectManager.getProjects()
                });

                this.loading("", false);
            }
            else {
                this.loading(result['text'], false);
            }
         
        });        
    }
}

export default ProjectStore
