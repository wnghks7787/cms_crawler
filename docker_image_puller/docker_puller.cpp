#include <iostream>
#include <vector>
#include <fstream>
#include <string>
#include <sstream>

#include <ctime>
#include <unistd.h>
#include <sys/wait.h>

using namespace std;

vector< pair<string, string> > find_cms(string path);
vector<string> split(string str, char Delimiter);

int main()
{
	time_t current_timer;
	struct tm* t;

	string resource_path = "../resources";

	vector< pair<string, string> > CMSes = find_cms(resource_path);

	int image_count = 0;

	for(int i = 0 ; i < CMSes.size() ; i++)
	{
		string cms_lib = CMSes[i].first;
		string cms_name = CMSes[i].second;

		int current_count = 0;

		cout << "⚙️ Download CMS: " << cms_name << endl;

		string version_folder = "../docker_hub_library_version/";
		string file_path = version_folder + cms_name + "_version";

		// Version Info File Open
		ifstream version_info;
		cout << "Open file from " << file_path << endl;
		version_info.open(file_path);
		
		// Fail to open file
		if(!version_info)
		{
			cerr << "❌ Fail to open file..." << endl << endl;
			continue;
		}
		// Success to open file
		cout << "✅ Successfully open file!" << endl;

		char version_num[256] = {0, };
		while(version_info.getline(version_num, 256))
		{
			cout << 80 - image_count%80 << " images left before sleep!" << endl;

			// Waiting for docker. 80 images with 2 hours
			if(image_count != 0 && image_count % 80 == 0)
			{
				current_timer = time(NULL);
				t = localtime(&current_timer);

				cout << "⏳ 80 images downloaded time: " << t->tm_mon + 1 << ". " << t->tm_mday << ". " << t->tm_hour << ":" << t->tm_min << endl;
				cout << "Next starting time: " << t->tm_hour + 2 << ":" << t->tm_min << endl;
				cout << "💤 Waiting for 2 Hours..." << endl;

				sleep(7200);

				cout << "🚀 Now restart!!!" << endl;
			}

			cout << "🐳 Start pulling docker with version " << version_num << "..." << endl;

			// check cms name
			string cms_name_ver;
			if(cms_lib == "library")
				cms_name_ver = cms_name + ":" + (string)version_num;
			else
				cms_name_ver = cms_lib + "/" + cms_name + ":" + (string)version_num;


			// make child processor
			pid_t pid = fork();

			if(pid == 0)
			{
				char *args[] = {
					(char *) "docker",
					(char *) "pull",
					(char *) cms_name_ver.c_str(),
					NULL
				};
				execvp("docker", args);
				perror("❌ Failed to pulling image...");
				return 1;
			}
			else if(pid > 0)
			{
				int status;
				waitpid(pid, &status, 0);
				image_count++;
				current_count++;
			}
			else
			{
				perror("❌ Fork failed...");
			}
		}

		// Notice Current Successed
		cout << "🎉 Total " << current_count << " images pulled!" << endl;

		// File Closing
		cout << " ...END! File closing" << endl;
		version_info.close();

		cout << endl;
	}

	return 0;
}


vector< pair<string, string> > find_cms(string path)
{
	vector< pair<string, string> > result_cms;

	string docker_hub_library = path + "/docker_hub_library.csv";

	ifstream cms_library;
	cms_library.open(docker_hub_library);

	char cms_name[256] = {0, };
	while(cms_library.getline(cms_name, 256))
	{
		vector<string> cms_vec = split(cms_name, ',');

		result_cms.push_back(make_pair(cms_vec[0], cms_vec[1]));
	}

	cms_library.close();

	return result_cms;
}

vector<string> split(string str, char Delimiter)
{
	istringstream iss(str);
	string buffer;

	vector<string> result;

	while(getline(iss, buffer, Delimiter))
	{
		result.push_back(buffer);
	}
	
	return result;
}